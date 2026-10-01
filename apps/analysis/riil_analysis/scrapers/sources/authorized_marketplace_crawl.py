from datetime import UTC, datetime
import hashlib
import json
import re
from typing import Any, Iterable
from urllib.parse import (
    parse_qsl,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

from bs4 import BeautifulSoup

from riil_analysis.ingestion.models import RawVehicleObservation
from riil_analysis.scrapers.base import VehicleSourceAdapter
from riil_analysis.scrapers.polite_http import PoliteHttpClient


KNOWN_MAKES = (
    "Mercedes-Benz",
    "Mercedes Benz",
    "Mitsubishi",
    "Volkswagen",
    "Chevrolet",
    "Daihatsu",
    "Hyundai",
    "Peugeot",
    "Subaru",
    "Toyota",
    "Nissan",
    "Suzuki",
    "Isuzu",
    "Honda",
    "Mazda",
    "Wuling",
    "Lexus",
    "Ford",
    "Hino",
    "Jeep",
    "BMW",
    "Kia",
    "Audi",
    "BYD",
)

KNOWN_REGIONS = (
    "DKI Jakarta",
    "Jawa Barat",
    "Jawa Timur",
    "Jawa Tengah",
    "Banten",
    "Bali",
    "Yogyakarta",
    "Sumatera Utara",
    "Sumatera Selatan",
    "Kalimantan Selatan",
    "Kalimantan Timur",
    "Sulawesi Selatan",
    "Sulawesi Utara",
)


class AuthorizedMarketplaceCrawler(VehicleSourceAdapter):
    """
    Sequential marketplace crawler for sources where the operator has explicit
    permission to crawl.

    Safety / load characteristics:
      - authorization reference required;
      - one request at a time;
      - >= 1 second between requests, 2 seconds by default;
      - default 10 and hard 50 detail pages per run;
      - 429/503 backoff with Retry-After support;
      - no CAPTCHA bypass, proxy rotation, or access-control evasion.
    """

    provider_name: str
    allowed_hosts: tuple[str, ...]
    default_start_url: str
    default_detail_limit = 10
    hard_detail_limit = 50
    max_index_pages = 5

    def fetch(self) -> bytes:
        if not self.authorization_reference:
            raise ValueError(
                f"{self.source_id} requires --authorization-ref documenting "
                "the marketplace permission for live crawling."
            )

        start_url = self.start_url or self.default_start_url
        self._validate_url(start_url)

        requested_limit = self.fetch_limit or self.default_detail_limit
        detail_limit = min(max(requested_limit, 1), self.hard_detail_limit)

        detail_urls: list[str] = []
        seen: set[str] = set()
        index_pages_fetched = 0

        with PoliteHttpClient(
            delay_seconds=self.request_delay_seconds,
            user_agent=(
                "FinEngine/0.1 authorized-marketplace-crawler "
                f"({self.provider_name})"
            ),
        ) as client:
            for page_number in range(1, self.max_index_pages + 1):
                page_url = self._page_url(start_url, page_number)
                self._validate_url(page_url)

                response = client.get(page_url)
                index_pages_fetched += 1

                for detail_url in self._discover_detail_urls(
                    response.text,
                    base_url=str(response.url),
                ):
                    if detail_url in seen:
                        continue
                    seen.add(detail_url)
                    detail_urls.append(detail_url)

                    if len(detail_urls) >= detail_limit:
                        break

                if len(detail_urls) >= detail_limit:
                    break

            documents: list[dict[str, str]] = []
            for detail_url in detail_urls[:detail_limit]:
                self._validate_url(detail_url)
                try:
                    response = client.get(detail_url)
                except Exception:
                    # One bad/removed listing should not terminate the whole run.
                    continue

                documents.append(
                    {
                        "url": str(response.url),
                        "html": response.text,
                    }
                )

        if not documents:
            raise ValueError(
                f"{self.source_id} discovered no usable detail pages. "
                "The supplied start URL may be too narrow, the site layout "
                "may have changed, or the page may require browser rendering."
            )

        return json.dumps(
            {
                "provider": self.provider_name,
                "authorization_reference": self.authorization_reference,
                "request_delay_seconds": self.request_delay_seconds,
                "index_pages_fetched": index_pages_fetched,
                "documents": documents,
            },
            ensure_ascii=False,
        ).encode("utf-8")

    def parse(self, payload: bytes) -> list[RawVehicleObservation]:
        bundle = json.loads(payload.decode("utf-8"))
        records: list[RawVehicleObservation] = []

        for document in bundle.get("documents", []):
            record = self._parse_detail(
                document["html"],
                source_url=document["url"],
                observed_at=datetime.now(UTC),
            )
            if record is not None:
                records.append(record)

        if not records:
            raise ValueError(
                f"{self.source_id} fetched detail pages but could not parse "
                "any vehicle listings."
            )

        return records

    def _discover_detail_urls(
        self,
        html: str,
        *,
        base_url: str,
    ) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = str(anchor.get("href"))
            absolute = urljoin(base_url, href)
            absolute = absolute.split("#", 1)[0]

            try:
                self._validate_url(absolute)
            except ValueError:
                continue

            if not self._is_detail_url(absolute):
                continue

            if absolute in seen:
                continue

            seen.add(absolute)
            urls.append(absolute)

        return urls

    def _parse_detail(
        self,
        html: str,
        *,
        source_url: str,
        observed_at: datetime,
    ) -> RawVehicleObservation | None:
        soup = BeautifulSoup(html, "html.parser")
        text = " ".join(soup.get_text(" ", strip=True).split())
        jsonld = list(self._jsonld_objects(soup))

        title = self._first_value(
            self._jsonld_value(jsonld, ("name",)),
            self._heading_or_title(soup),
        )
        if not title:
            return None

        make = self._first_value(
            self._jsonld_brand(jsonld),
            self._extract_make(title),
        )
        year = self._first_value(
            self._jsonld_value(
                jsonld,
                ("vehicleModelDate", "productionDate"),
            ),
            self._extract_year(title),
            self._extract_year(text),
        )
        price = self._first_value(
            self._jsonld_price(jsonld),
            self._extract_price(text),
        )

        if not (make and year and price):
            return None

        model = self._jsonld_model(jsonld)
        descriptor = self._descriptor_from_title(
            title,
            make=str(make),
            year=str(year),
        )

        type_name = model or descriptor
        if not type_name:
            return None

        region = self._first_value(
            self._jsonld_region(jsonld),
            self._extract_region(text),
            "Indonesia",
        )
        currency = self._first_value(
            self._jsonld_currency(jsonld),
            "IDR",
        )

        listing_id = self._first_value(
            self._jsonld_value(
                jsonld,
                ("sku", "productID", "identifier"),
            ),
            self._listing_id_from_url(source_url),
        )
        if not listing_id:
            listing_id = hashlib.sha256(
                source_url.encode("utf-8")
            ).hexdigest()[:20]

        metadata: dict[str, Any] = {
            "provider": self.provider_name,
            "access_basis": "authorized_crawl",
            "authorization_reference": self.authorization_reference,
            "request_delay_seconds": self.request_delay_seconds,
            "listing_title": title,
            "parser_version": "marketplace_jsonld_html_v1",
        }

        mileage = self._first_value(
            self._jsonld_mileage(jsonld),
            self._extract_mileage(text),
        )
        if mileage is not None:
            metadata["mileage"] = mileage

        transmission = self._first_value(
            self._jsonld_value(
                jsonld,
                ("vehicleTransmission",),
            ),
            self._extract_transmission(text),
        )
        if transmission:
            metadata["transmission"] = transmission

        fuel = self._first_value(
            self._jsonld_value(jsonld, ("fuelType",)),
            self._extract_fuel(text),
        )
        if fuel:
            metadata["fuel"] = fuel

        return RawVehicleObservation(
            source=self.source_id,
            source_record_id=str(listing_id),
            source_url=source_url,
            observed_at=observed_at,
            make_raw=str(make),
            model_raw=str(model) if model else None,
            type_raw=str(type_name),
            year_raw=str(year),
            region_raw=str(region),
            price_raw=str(price),
            price_kind="listing",
            currency=str(currency),
            category_raw="MARKETPLACE LISTING",
            metadata=metadata,
        )

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Unsupported crawl URL scheme: {url}")

        host = (parsed.hostname or "").lower()
        if not any(
            host == allowed or host.endswith("." + allowed)
            for allowed in self.allowed_hosts
        ):
            raise ValueError(
                f"{self.source_id} may only crawl its authorized hosts; "
                f"got {host!r}"
            )

    @staticmethod
    def _replace_query(url: str, updates: dict[str, str]) -> str:
        parsed = urlparse(url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.update(updates)
        return urlunparse(
            parsed._replace(query=urlencode(query, doseq=True))
        )

    def _page_url(self, start_url: str, page_number: int) -> str:
        if page_number == 1:
            return start_url
        return self._replace_query(
            start_url,
            {"page": str(page_number)},
        )

    def _is_detail_url(self, url: str) -> bool:
        raise NotImplementedError

    @staticmethod
    def _heading_or_title(soup: BeautifulSoup) -> str | None:
        heading = soup.find("h1")
        if heading:
            value = " ".join(heading.get_text(" ", strip=True).split())
            if value:
                return value

        if soup.title and soup.title.string:
            return " ".join(soup.title.string.split())

        return None

    @staticmethod
    def _first_value(*values: Any) -> Any:
        for value in values:
            if value not in (None, ""):
                return value
        return None

    @staticmethod
    def _jsonld_objects(
        soup: BeautifulSoup,
    ) -> Iterable[dict[str, Any]]:
        for script in soup.find_all("script", type="application/ld+json"):
            raw = script.string or script.get_text()
            if not raw.strip():
                continue

            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                continue

            yield from AuthorizedMarketplaceCrawler._walk_json(value)

    @staticmethod
    def _walk_json(value: Any) -> Iterable[dict[str, Any]]:
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from AuthorizedMarketplaceCrawler._walk_json(child)
        elif isinstance(value, list):
            for child in value:
                yield from AuthorizedMarketplaceCrawler._walk_json(child)

    @staticmethod
    def _jsonld_value(
        objects: list[dict[str, Any]],
        keys: tuple[str, ...],
    ) -> Any:
        for obj in objects:
            for key in keys:
                value = obj.get(key)
                if isinstance(value, (str, int, float)) and value != "":
                    return value
        return None

    @staticmethod
    def _jsonld_brand(objects: list[dict[str, Any]]) -> str | None:
        for obj in objects:
            brand = obj.get("brand")
            if isinstance(brand, str):
                return brand
            if isinstance(brand, dict):
                name = brand.get("name")
                if isinstance(name, str):
                    return name
        return None

    @staticmethod
    def _jsonld_model(objects: list[dict[str, Any]]) -> str | None:
        for obj in objects:
            model = obj.get("model")
            if isinstance(model, str):
                return model
            if isinstance(model, dict):
                name = model.get("name")
                if isinstance(name, str):
                    return name
        return None

    @staticmethod
    def _jsonld_price(objects: list[dict[str, Any]]) -> Any:
        for obj in objects:
            for key in ("price", "lowPrice"):
                value = obj.get(key)
                if isinstance(value, (str, int, float)):
                    return value

            offers = obj.get("offers")
            if isinstance(offers, dict):
                for key in ("price", "lowPrice"):
                    value = offers.get(key)
                    if isinstance(value, (str, int, float)):
                        return value
        return None

    @staticmethod
    def _jsonld_currency(objects: list[dict[str, Any]]) -> str | None:
        for obj in objects:
            value = obj.get("priceCurrency")
            if isinstance(value, str):
                return value

            offers = obj.get("offers")
            if isinstance(offers, dict):
                value = offers.get("priceCurrency")
                if isinstance(value, str):
                    return value
        return None

    @staticmethod
    def _jsonld_region(objects: list[dict[str, Any]]) -> str | None:
        for obj in objects:
            address = obj.get("address")
            if isinstance(address, dict):
                for key in ("addressRegion", "addressLocality"):
                    value = address.get(key)
                    if isinstance(value, str):
                        return value
        return None

    @staticmethod
    def _jsonld_mileage(objects: list[dict[str, Any]]) -> Any:
        for obj in objects:
            mileage = obj.get("mileageFromOdometer")
            if isinstance(mileage, dict):
                value = mileage.get("value")
                if isinstance(value, (str, int, float)):
                    return value
            if isinstance(mileage, (str, int, float)):
                return mileage
        return None

    @staticmethod
    def _extract_make(text: str) -> str | None:
        upper = text.upper()
        for make in KNOWN_MAKES:
            if re.search(rf"\b{re.escape(make.upper())}\b", upper):
                return make
        return None

    @staticmethod
    def _extract_year(text: str) -> str | None:
        match = re.search(r"\b((?:19|20)\d{2})\b", text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_price(text: str) -> str | None:
        match = re.search(
            r"\bRp\.?\s*([0-9][0-9. ]{4,})",
            text,
            flags=re.IGNORECASE,
        )
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_region(text: str) -> str | None:
        lower = text.lower()
        for region in KNOWN_REGIONS:
            if region.lower() in lower:
                return region
        return None

    @staticmethod
    def _extract_mileage(text: str) -> str | None:
        patterns = (
            r"(?:Mileage|Jarak Tempuh|Odometer)\s*[:\-]?\s*"
            r"([0-9][0-9., ]*(?:\s*-\s*[0-9][0-9., ]*)?\s*K?\s*KM)",
            r"\b([0-9]{1,3}\s*-\s*[0-9]{1,3}K\s*KM)\b",
        )
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return " ".join(match.group(1).split())
        return None

    @staticmethod
    def _extract_transmission(text: str) -> str | None:
        for transmission in ("Automatic", "Manual", "CVT"):
            if re.search(
                rf"\b{re.escape(transmission)}\b",
                text,
                flags=re.IGNORECASE,
            ):
                return transmission
        return None

    @staticmethod
    def _extract_fuel(text: str) -> str | None:
        mapping = {
            "Petrol": ("petrol", "bensin", "gasoline"),
            "Diesel": ("diesel", "solar"),
            "Electric": ("electric", "listrik"),
            "Hybrid": ("hybrid",),
        }
        lower = text.lower()
        for canonical, terms in mapping.items():
            if any(term in lower for term in terms):
                return canonical
        return None

    @staticmethod
    def _descriptor_from_title(
        title: str,
        *,
        make: str,
        year: str,
    ) -> str | None:
        value = title
        value = re.sub(
            rf"^\s*{re.escape(year)}\s+",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            rf"\b{re.escape(make)}\b",
            "",
            value,
            count=1,
            flags=re.IGNORECASE,
        )
        value = value.split(" - ", 1)[0]
        value = " ".join(value.strip(" :-|").split())
        return value or None

    @staticmethod
    def _listing_id_from_url(url: str) -> str | None:
        parsed = urlparse(url)
        match = re.search(r"(?:iid[-_/]?|/)(\d{6,})(?:/)?$", parsed.path)
        if match:
            return match.group(1)

        match = re.search(r"-iid-(\d+)", parsed.path)
        return match.group(1) if match else None


class OlxAuthorizedCrawler(AuthorizedMarketplaceCrawler):
    source_id = "olx_authorized_crawl"
    source_url = "https://www.olx.co.id/"
    provider_name = "OLX Indonesia"
    allowed_hosts = ("olx.co.id",)
    default_start_url = "https://www.olx.co.id/mobil-bekas_c198"

    def _is_detail_url(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        return "/item/" in path or "-iid-" in path


class Mobil123AuthorizedCrawler(AuthorizedMarketplaceCrawler):
    source_id = "mobil123_authorized_crawl"
    source_url = "https://www.mobil123.com/"
    provider_name = "Mobil123"
    allowed_hosts = ("mobil123.com",)
    default_start_url = "https://www.mobil123.com/mobil-bekas-dijual"

    def _is_detail_url(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        return bool(re.search(r"/dijual/.+/\d+/?$", path))

    def _page_url(self, start_url: str, page_number: int) -> str:
        if page_number == 1:
            return start_url
        return self._replace_query(
            start_url,
            {
                "page_number": str(page_number),
                "page_size": "25",
            },
        )


class CarmudiAuthorizedCrawler(AuthorizedMarketplaceCrawler):
    source_id = "carmudi_authorized_crawl"
    source_url = "https://www.carmudi.co.id/"
    provider_name = "Carmudi Indonesia"
    allowed_hosts = ("carmudi.co.id",)
    default_start_url = (
        "https://www.carmudi.co.id/mobil-bekas-dijual/indonesia"
    )

    def _is_detail_url(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        return bool(
            re.search(r"/(?:en/for-sale|id/dijual|dijual)/.+/\d+/?$", path)
        )

    def _page_url(self, start_url: str, page_number: int) -> str:
        if page_number == 1:
            return start_url
        return self._replace_query(
            start_url,
            {
                "page_number": str(page_number),
                "page_size": "25",
            },
        )
