"""Regional motor-vehicle statistics from BPS official source tables."""

import csv
from datetime import UTC, datetime
import hashlib
import io
from pathlib import Path
import re

from bs4 import BeautifulSoup
import httpx

from riil_analysis.config import FIN_ENGINE_USER_AGENT, latest_official_source
from riil_analysis.regional import RegionalVehicleStatisticInput


SOURCE_CONFIG = latest_official_source("regional_vehicle_stock")
SUPPORTED_INPUT_EXTENSIONS = frozenset({".html", ".htm", ".csv"})
MIN_REGIONAL_ROWS = 10


class BpsVehicleStockAdapter:
    """Fetch and parse the latest configured official BPS vehicle-stock table.

    The BPS website may render table data in the browser rather than in the
    initial HTTP response. A CSV exported from the BPS table is supported as
    an explicit, auditable offline import; it is never silently substituted.
    """

    source_id = SOURCE_CONFIG.source_id
    source_url = SOURCE_CONFIG.source_url
    year = SOURCE_CONFIG.release_year

    def __init__(self) -> None:
        self.input_path: Path | None = None

    def set_input_path(self, path: Path | None) -> None:
        """Use an official BPS HTML or CSV export instead of a live request."""
        self.input_path = path

    def fetch(self) -> bytes:
        if self.input_path is not None:
            if self.input_path.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
                raise ValueError(
                    "BPS --input-file accepts a saved official BPS HTML page "
                    "(.html/.htm) or table export (.csv)."
                )
            return self.input_path.read_bytes()

        with httpx.Client(
            follow_redirects=True,
            timeout=SOURCE_CONFIG.timeout_seconds,
            headers={
                "User-Agent": FIN_ENGINE_USER_AGENT,
                "Accept": SOURCE_CONFIG.accept_header,
            },
        ) as client:
            response = client.get(self.source_url)
            response.raise_for_status()
        return response.content

    def _input_rows(self, payload: bytes) -> list[list[str]]:
        if self.input_path is not None and self.input_path.suffix.lower() == ".csv":
            try:
                text = payload.decode("utf-8-sig")
            except UnicodeDecodeError as error:
                raise ValueError(
                    "BPS CSV must be UTF-8. Re-export the official table as UTF-8 CSV."
                ) from error

            try:
                dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
            except csv.Error as error:
                raise ValueError(
                    "BPS CSV delimiter could not be identified. Export the table "
                    "with comma, semicolon, or tab separated fields."
                ) from error

            rows = [
                [self._clean_cell(cell) for cell in row]
                for row in csv.reader(io.StringIO(text), dialect)
            ]
            # This adapter is bound to one BPS publication year. A multi-year
            # CSV or a wrongly selected year must not silently become 2025 data.
            header_text = " ".join(
                cell for row in rows[:20] for cell in row
            )
            if not re.search(rf"\b{self.year}\b", header_text):
                raise ValueError(
                    f"BPS CSV does not identify the configured source year "
                    f"{self.year} in its header. Verify the downloaded year "
                    "on BPS before importing; do not relabel older data."
                )
            return rows

        soup = BeautifulSoup(payload, "html.parser")
        return [
            [
                self._clean_cell(cell.get_text(" ", strip=True))
                for cell in row.find_all(["th", "td"])
            ]
            for row in soup.find_all("tr")
        ]

    def parse(self, payload: bytes) -> list[RegionalVehicleStatisticInput]:
        observed_at = datetime.now(UTC)
        records: dict[str, RegionalVehicleStatisticInput] = {}

        acquisition = "public_statistics_table"
        provenance: dict[str, str] = {}
        if self.input_path is not None:
            suffix = self.input_path.suffix.lower()
            acquisition = (
                "manual_official_csv_export"
                if suffix == ".csv"
                else "manual_official_html_snapshot"
            )
            provenance = {
                "import_filename": self.input_path.name,
                "import_sha256": hashlib.sha256(payload).hexdigest(),
            }

        for cells in self._input_rows(payload):
            cells = [cell for cell in cells if cell]
            if len(cells) < 6:
                continue

            prefix_cells, value_cells = cells[:-5], cells[-5:]
            region = next(
                (
                    cell for cell in reversed(prefix_cells)
                    if re.search(r"[A-Za-z]", cell)
                ),
                None,
            )
            if not region:
                continue

            try:
                passenger_cars, buses, trucks, motorcycles, total = [
                    self._parse_count(value) for value in value_cells
                ]
            except ValueError:
                continue

            # Counts and their published sum must agree. Avoid accidentally
            # ingesting other numeric tables or a shifted CSV year/column.
            if passenger_cars + buses + trucks + motorcycles != total:
                continue

            if region in records:
                raise ValueError(
                    f"BPS source contains duplicate numeric rows for {region!r}. "
                    "Check the export and year columns before persistence."
                )

            records[region] = RegionalVehicleStatisticInput(
                source=self.source_id,
                source_url=self.source_url,
                observed_at=observed_at,
                year=self.year,
                region=region,
                passenger_cars=passenger_cars,
                buses=buses,
                trucks=trucks,
                motorcycles=motorcycles,
                total=total,
                metadata={
                    "publisher": SOURCE_CONFIG.publisher,
                    "table_year": self.year,
                    "publication": SOURCE_CONFIG.publication_label,
                    "reference_type": "official_regional_vehicle_stock",
                    "acquisition": acquisition,
                    **provenance,
                },
            )

        if len(records) < MIN_REGIONAL_ROWS:
            raise ValueError(
                "BPS vehicle-stock table produced too few validated regional "
                "rows. The public page may render its table with JavaScript. "
                "Download the official 2025 table as CSV from bps.go.id and "
                "import it using 'yarn ingest --source vehicle_stock_latest "
                "--input-file ../../data/generated/bps-2025.csv --persist-db'. "
                "No incomplete source data were persisted."
            )

        return list(records.values())

    def run(self) -> list[RegionalVehicleStatisticInput]:
        return self.parse(self.fetch())

    @staticmethod
    def _clean_cell(value: str) -> str:
        return " ".join(value.replace("\xa0", " ").split()).strip()

    @staticmethod
    def _parse_count(value: str) -> int:
        # Official BPS thousands separators are periods (ID) or commas (EN).
        # Temporary/revised-data footnotes may follow a number; do not turn
        # footnote digits or missing-data markers into vehicle counts.
        match = re.fullmatch(
            r"\s*(\d{1,3}(?:[.,]\d{3})*|\d+)\s*(?:\*{1,3}|[erabc])?\s*",
            value,
            flags=re.IGNORECASE,
        )
        if match is None:
            raise ValueError(f"Invalid BPS vehicle count: {value!r}")
        return int(match.group(1).replace(".", "").replace(",", ""))
