from datetime import UTC, datetime
import json
import re
import time
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import httpx

from riil_analysis.ingestion.models import RawVehicleObservation
from riil_analysis.scrapers.base import VehicleSourceAdapter


class DjpVehicleAuctionLimitsAdapter(VehicleSourceAdapter):
    """
    Vehicle auction-limit observations from official DJP auction announcements.

    The captured price is the published auction limit/reserve value, not a
    retail listing price and not the final auction transaction price.
    """

    source_id = "djp_vehicle_auction_limits"
    source_url = "https://www.pajak.go.id/info-lelang-page/"
    default_max_details = 25

    VEHICLE_TERMS = (
        "mobil",
        "motor",
        "kendaraan",
        "truk",
        "truck",
        "toyota",
        "daihatsu",
        "honda",
        "nissan",
        "suzuki",
        "mitsubishi",
        "isuzu",
        "mazda",
        "ford",
        "hino",
        "hyundai",
        "kia",
        "wuling",
        "bmw",
        "mercedes",
        "jeep",
    )

    MAKE_ALIASES = (
        ("MERCEDES-BENZ", "Mercedes-Benz"),
        ("MERCEDES BENZ", "Mercedes-Benz"),
        ("MITSUBISHI", "Mitsubishi"),
        ("MITSHUBISHI", "Mitsubishi"),
        ("VOLKSWAGEN", "Volkswagen"),
        ("CHEVROLET", "Chevrolet"),
        ("DAIHATSU", "Daihatsu"),
        ("HYUNDAI", "Hyundai"),
        ("PEUGEOT", "Peugeot"),
        ("SUBARU", "Subaru"),
        ("TOYOTA", "Toyota"),
        ("NISSAN", "Nissan"),
        ("SUZUKI", "Suzuki"),
        ("ISUZU", "Isuzu"),
        ("HONDA", "Honda"),
        ("MAZDA", "Mazda"),
        ("WULING", "Wuling"),
        ("LEXUS", "Lexus"),
        ("FORD", "Ford"),
        ("HINO", "Hino"),
        ("JEEP", "Jeep"),
        ("BMW", "BMW"),
        ("KIA", "Kia"),
        ("AUDI", "Audi"),
    )

    def fetch(self) -> bytes:
        max_details = self.fetch_limit or self.default_max_details

        with httpx.Client(
            follow_redirects=True,
            timeout=30.0,
            headers={
                "User-Agent": "FinEngine/0.1 (+https://riil.id)",
                "Accept": "text/html,application/xhtml+xml",
            },
        ) as client:
            response = client.get(self.source_url)
            response.raise_for_status()
            detail_urls = self._discover_detail_urls(response.text)

            documents: list[dict[str, str]] = []
            for detail_url in detail_urls[:max_details]:
                # Keep this deliberately low-frequency; this is a public
                # government information source, not a high-throughput crawl.
                time.sleep(0.2)
                try:
                    detail = client.get(detail_url)
                    detail.raise_for_status()
                except httpx.HTTPError:
                    continue

                documents.append(
                    {
                        "url": str(detail.url),
                        "html": detail.text,
                    }
                )

        return json.dumps(
            {
                "documents": documents,
            },
            ensure_ascii=False,
        ).encode("utf-8")

    def parse(self, payload: bytes) -> list[RawVehicleObservation]:
        bundle = json.loads(payload.decode("utf-8"))
        observed_at = datetime.now(UTC)
        records: list[RawVehicleObservation] = []

        for document in bundle.get("documents", []):
            record = self._parse_detail(
                document["html"],
                source_url=document["url"],
                observed_at=observed_at,
            )
            if record is not None:
                records.append(record)

        if not records:
            raise ValueError(
                "No single-vehicle DJP auction-limit observations could be "
                "parsed. The source page may have changed or the discovered "
                "announcements may not contain supported vehicle details."
            )

        return records

    def _discover_detail_urls(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            label = " ".join(anchor.get_text(" ", strip=True).split())
            href = str(anchor.get("href"))
            lower_label = label.lower()

            if not any(term in lower_label for term in self.VEHICLE_TERMS):
                continue

            absolute = urljoin(self.source_url, href)
            parsed = urlparse(absolute)

            if not parsed.hostname or not parsed.hostname.endswith("pajak.go.id"):
                continue
            if "/pengumuman/" not in parsed.path:
                continue

            canonical = absolute.split("#", 1)[0]
            if canonical in seen:
                continue

            seen.add(canonical)
            urls.append(canonical)

        return urls

    def _parse_detail(
        self,
        html: str,
        *,
        source_url: str,
        observed_at: datetime,
    ) -> RawVehicleObservation | None:
        soup = BeautifulSoup(html, "html.parser")
        title = self._extract_title(soup)
        text = " ".join(soup.get_text(" ", strip=True).split())

        if not title:
            return None

        make = self._extract_make(title)
        year = self._extract_year(title, text)
        limit_value = self._extract_limit_value(text)

        if not (make and year and limit_value):
            return None

        type_name = self._extract_type_name(title, make)
        if not type_name:
            return None

        slug = urlparse(source_url).path.rstrip("/").split("/")[-1]
        if not slug:
            return None

        metadata: dict[str, object] = {
            "announcement_title": title,
            "reference_type": "official_auction_limit",
        }

        deposit = self._extract_money_after_label(text, "uang jaminan")
        if deposit is not None:
            metadata["deposit"] = deposit

        mileage = self._extract_mileage(text)
        if mileage is not None:
            metadata["mileage_km"] = mileage

        auction_date = self._extract_labeled_value(text, "Tanggal Lelang")
        if auction_date:
            metadata["auction_date_raw"] = auction_date

        auction_location = self._extract_labeled_value(text, "Tempat Lelang")
        if auction_location:
            metadata["auction_location_raw"] = auction_location

        return RawVehicleObservation(
            source=self.source_id,
            source_record_id=slug,
            source_url=source_url,
            observed_at=observed_at,
            make_raw=make,
            type_raw=type_name,
            year_raw=year,
            region_raw="Indonesia",
            price_raw=limit_value,
            price_kind="auction_limit",
            currency="IDR",
            category_raw="VEHICLE AUCTION",
            metadata=metadata,
        )

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str | None:
        heading = soup.find("h1")
        if heading:
            title = " ".join(heading.get_text(" ", strip=True).split())
            if title:
                return title

        if soup.title and soup.title.string:
            title = " ".join(soup.title.string.split())
            title = re.sub(
                r"\s*\|\s*Direktorat Jenderal Pajak.*$",
                "",
                title,
                flags=re.IGNORECASE,
            )
            return title or None

        return None

    @classmethod
    def _extract_make(cls, title: str) -> str | None:
        upper = title.upper()
        for raw_make, canonical in cls.MAKE_ALIASES:
            if re.search(rf"\b{re.escape(raw_make)}\b", upper):
                return canonical
        return None

    @staticmethod
    def _extract_year(title: str, text: str) -> str | None:
        patterns = (
            r"\b[Tt]ahun(?:\s+(?:Pembuatan|Perakitan))?\s*[:\-]?\s*((?:19|20)\d{2})\b",
            r"\b((?:19|20)\d{2})\b",
        )

        for candidate in (title, text):
            for pattern in patterns:
                match = re.search(pattern, candidate)
                if match:
                    return match.group(1)

        return None

    @staticmethod
    def _extract_limit_value(text: str) -> str | None:
        match = re.search(
            r"(?:nilai|harga)\s+limit(?:\s+lelang)?"
            r"[^0-9]{0,50}(?:rp\.?\s*)"
            r"([0-9][0-9. ]*)",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        return match.group(1).strip()

    @staticmethod
    def _extract_money_after_label(text: str, label: str) -> int | None:
        match = re.search(
            rf"{re.escape(label)}[^0-9]{{0,50}}(?:rp\.?\s*)"
            r"([0-9][0-9. ]*)",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        digits = re.sub(r"[^0-9]", "", match.group(1))
        return int(digits) if digits else None

    @staticmethod
    def _extract_mileage(text: str) -> int | None:
        match = re.search(
            r"(?:odometer|kilometer)\s*[:\-]?\s*([0-9][0-9., ]*)\s*km\b",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        digits = re.sub(r"[^0-9]", "", match.group(1))
        return int(digits) if digits else None

    @staticmethod
    def _extract_labeled_value(text: str, label: str) -> str | None:
        match = re.search(
            rf"{re.escape(label)}\s*[:\-]?\s*(.{{1,120}}?)"
            r"(?=\s+(?:Batas Pendaftaran|Tempat Lelang|URL Lelang|"
            r"Nilai Limit|Uang Jaminan|Proses lelang|$))",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        return " ".join(match.group(1).split())

    @staticmethod
    def _extract_type_name(title: str, make: str) -> str | None:
        match = re.search(re.escape(make), title, flags=re.IGNORECASE)
        if not match:
            return None

        descriptor = title[match.end():]
        descriptor = descriptor.lstrip(" /:-(")

        stop_patterns = (
            r"\b[Tt]ahun\b",
            r"\bKPP\b",
            r"\bdi\s+(?:Kota|Kabupaten|Provinsi)\b",
            r"\b(?:19|20)\d{2}\b",
        )

        end = len(descriptor)
        for pattern in stop_patterns:
            stop = re.search(pattern, descriptor)
            if stop:
                end = min(end, stop.start())

        descriptor = descriptor[:end].rstrip(" )-,:")
        descriptor = " ".join(descriptor.split())

        return descriptor or None
