from datetime import UTC, datetime
import io
import re

import httpx
import pdfplumber

from riil_analysis.ingestion.models import RawVehicleObservation
from riil_analysis.scrapers.base import VehicleSourceAdapter


class KemendagriNjkb2025Adapter(VehicleSourceAdapter):
    """
    Official 2025 NJKB reference values from Permendagri No. 7/2025.

    This is a government tax/reference-value source. It is not a live
    transaction-price or marketplace-listing feed and must not be labelled
    as one by downstream analytics.
    """

    source_id = "kemendagri_njkb_2025"
    source_url = (
        "https://peraturan.bpk.go.id/Details/321612/"
        "permendagri-no-7-tahun-2025"
    )
    download_url = (
        "https://peraturan.bpk.go.id/Download/383357/"
        "Permendagri%20Nomor%207%20Tahun%202025.pdf"
    )

    def fetch(self) -> bytes:
        with httpx.Client(
            follow_redirects=True,
            timeout=60.0,
            headers={
                "User-Agent": "FinEngine/0.1 (+https://riil.id)",
                "Accept": "application/pdf",
            },
        ) as client:
            response = client.get(self.download_url)
            response.raise_for_status()

        payload = response.content
        if not payload.startswith(b"%PDF"):
            raise ValueError("NJKB source did not return a PDF payload.")

        return payload

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

        if not re.search(r"\b(?:19|20)\d{2}\b", year):
            return None

        if not re.search(r"\d", njkb):
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
            region_raw="Indonesia",
            price_raw=njkb,
            price_kind="njkb",
            currency="IDR",
            category_raw=category,
            metadata={
                "row_number": number,
                "coding": coding,
                "weight": weight,
                "dp_pkb": dp_pkb,
                "regulation": "Permendagri No. 7 Tahun 2025",
                "reference_type": "official_njkb",
            },
        )

    @staticmethod
    def _clean_cell(value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.replace("\n", " ").split())
        return cleaned or None
