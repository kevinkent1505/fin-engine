from datetime import UTC, datetime
import hashlib
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
    # Official government-hosted JDIH copy of the 2025 regulation.
    government_mirror_urls = (
        "https://jdih.acehprov.go.id/dih/view/"
        "4c313164-4a46-4ca0-a6b1-a76b29e5ca77",
    )
    download_urls = SOURCE_CONFIG.download_urls + government_mirror_urls

    def fetch(self) -> bytes:
        self._downloaded_from = None
        self._content_sha256 = None

        # Support explicitly downloaded official snapshots if cloud access is
        # restricted. Do not silently substitute unrelated PDFs.
        if self.input_path is not None:
            if self.input_path.suffix.lower() != ".pdf":
                raise ValueError("NJKB --input-file must be an official PDF (.pdf).")
            payload = self.input_path.read_bytes()
            if not payload.startswith(b"%PDF"):
                raise ValueError("NJKB --input-file was not a PDF.")
            self._downloaded_from = "manual_official_pdf_snapshot"
            self._content_sha256 = hashlib.sha256(payload).hexdigest()
            return payload

        failures: list[str] = []
        with httpx.Client(
            follow_redirects=True,
            timeout=SOURCE_CONFIG.timeout_seconds,
            headers={
                "User-Agent": FIN_ENGINE_USER_AGENT,
                "Accept": SOURCE_CONFIG.accept_header,
            },
        ) as client:
            for url in self.download_urls:
                try:
                    # Only BPK endpoints receive the BPK referer.
                    headers = (
                        {"Referer": SOURCE_CONFIG.source_url}
                        if url.startswith("https://peraturan.bpk.go.id/")
                        else {}
                    )
                    response = client.get(url, headers=headers)
                    response.raise_for_status()
                except httpx.HTTPError as error:
                    failures.append(f"{url}: {type(error).__name__}")
                    continue

                payload = response.content
                if payload.startswith(b"%PDF"):
                    self._downloaded_from = str(response.url)
                    self._content_sha256 = hashlib.sha256(payload).hexdigest()
                    return payload

                failures.append(
                    f"{url}: response was not a PDF "
                    f"(content-type={response.headers.get('content-type', 'unknown')})"
                )

        raise ValueError(
            "NJKB source could not be downloaded from official BPK or the "
            "government JDIH mirror. Download the official PDF and import "
            "with 'yarn ingest --source njkb_latest "
            "--input-file path/to/official.pdf --persist-db'. "
            + " | ".join(failures)
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
                "acquisition_url": getattr(self, "_downloaded_from", None),
                "document_sha256": getattr(self, "_content_sha256", None),
            },
        )

    @staticmethod
    def _clean_cell(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.replace("\n", " ").split())
        return cleaned or None
