from datetime import UTC, datetime
import io
import re

import httpx
import pdfplumber

from riil_analysis.config import FIN_ENGINE_USER_AGENT, latest_official_source
from riil_analysis.ingestion.models import RawVehicleObservation
from riil_analysis.scrapers.base import VehicleSourceAdapter


SOURCE_CONFIG = latest_official_source("njkb")


class KemendagriNjkbAdapter(VehicleSourceAdapter):
    """Fetch and parse the latest configured official Kemendagri NJKB release."""

    source_id = SOURCE_CONFIG.source_id
    source_url = SOURCE_CONFIG.source_url
    download_urls = SOURCE_CONFIG.download_urls

    def fetch(self) -> bytes:
        if not self.download_urls:
            raise ValueError(
                f"No download URL configured for official source {self.source_id}."
            )

        failures: list[str] = []

        with httpx.Client(
            follow_redirects=True,
            timeout=SOURCE_CONFIG.timeout_seconds,
            headers={
                "User-Agent": FIN_ENGINE_USER_AGENT,
                "Accept": SOURCE_CONFIG.accept_header,
                "Referer": SOURCE_CONFIG.source_url,
            },
        ) as client:
            for url in self.download_urls:
                try:
                    response = client.get(url)
                    response.raise_for_status()
                except httpx.HTTPError as error:
                    failures.append(f"{url}: {error}")
                    continue

                payload = response.content
                if payload.startswith(b"%PDF"):
                    return payload

                failures.append(
                    f"{url}: response was not a PDF "
                    f"(content-type={response.headers.get('content-type', 'unknown')})"
                )

        raise ValueError(
            "NJKB source could not be downloaded from any configured official "
            "document endpoint. " + " | ".join(failures)
        )

    def parse(self, payload: bytes) -> list[RawVehicleObservation]:
        fetched_at = datetime.now(UTC)
        records: list[RawVehicleObservation] = []
        current_category: str | None = None

        with pdfplumber.open(io.BytesIO(payload)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                category = self._category_from_page(text)
                if category:
                    current_category = category

                for table in page.extract_tables():
                    for row in table:
                        record = self._parse_table_row(
                            row,
                            category=current_category,
                            observed_at=fetched_at,
                        )
                        if record:
                            records.append(record)

        if not records:
            raise ValueError(
                "No NJKB vehicle rows could be parsed. "
                "The source document layout may have changed."
            )

        return records

    @staticmethod
    def _category_from_page(text: str) -> str | None:
        match = re.search(
            r"JENIS\s*:\s*([^\n]+)",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        return " ".join(match.group(1).split())

    @staticmethod
    def _looks_like_vehicle_row(
        *,
        make: str,
        year: str,
        njkb: str,
    ) -> bool:
        if re.fullmatch(r"(?:19|20)\d{2}", year) is None:
            return False
        if re.search(r"[A-Za-z]", make) is None:
            return False

        digits = re.sub(r"[^0-9]", "", njkb)
        return bool(digits and int(digits) > 0)

    def _parse_table_row(
        self,
        row: list[str | None],
        *,
        category: str | None,
        observed_at: datetime,
    ) -> RawVehicleObservation | None:
        cells = [self._clean_cell(cell) for cell in row]
        if len(cells) < 6:
            return None

        joined = " ".join(cell or "" for cell in cells).upper()
        if "MEREK" in joined and ("TH BUAT" in joined or "NJKB" in joined):
            return None

        number = cells[0]
        coding = cells[1] if len(cells) > 1 else None
        make = cells[2] if len(cells) > 2 else None
        type_name = cells[3] if len(cells) > 3 else None
        year = cells[4] if len(cells) > 4 else None
        njkb = cells[5] if len(cells) > 5 else None
        weight = cells[6] if len(cells) > 6 else None
        dp_pkb = cells[7] if len(cells) > 7 else None

        if not (make and type_name and year and njkb):
            return None

        if not self._looks_like_vehicle_row(
            make=make,
            year=year,
            njkb=njkb,
        ):
            return None

        record_id = "-".join(
            part
            for part in [
                coding or number or "row",
                year,
                make,
                type_name,
            ]
            if part
        )

        return RawVehicleObservation(
            source=self.source_id,
            source_record_id=record_id,
            source_url=self.source_url,
            observed_at=observed_at,
            make_raw=make,
            type_raw=type_name,
            year_raw=year,
            region_raw=SOURCE_CONFIG.default_region,
            price_raw=njkb,
            price_kind="njkb",
            currency="IDR",
            category_raw=category,
            metadata={
                "row_number": number,
                "coding": coding,
                "weight": weight,
                "dp_pkb": dp_pkb,
                "publisher": SOURCE_CONFIG.publisher,
                "release_year": SOURCE_CONFIG.release_year,
                "regulation": SOURCE_CONFIG.publication_label,
                "reference_type": "official_njkb",
            },
        )

    @staticmethod
    def _clean_cell(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.replace("\n", " ").split())
        return cleaned or None
