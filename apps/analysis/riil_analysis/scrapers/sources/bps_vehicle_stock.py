from datetime import UTC, datetime
from pathlib import Path
import re

from bs4 import BeautifulSoup
import httpx

from riil_analysis.config import FIN_ENGINE_USER_AGENT, latest_official_source
from riil_analysis.regional import RegionalVehicleStatisticInput


SOURCE_CONFIG = latest_official_source("regional_vehicle_stock")


class BpsVehicleStockAdapter:
    """Fetch and parse the latest configured official BPS vehicle-stock table."""

    source_id = SOURCE_CONFIG.source_id
    source_url = SOURCE_CONFIG.source_url
    year = SOURCE_CONFIG.release_year

    def __init__(self) -> None:
        self.input_path: Path | None = None

    def set_input_path(self, path: Path | None) -> None:
        """Use a saved HTML copy of the official BPS table when needed."""
        self.input_path = path

    def fetch(self) -> bytes:
        if self.input_path is not None:
            if self.input_path.suffix.lower() not in {".html", ".htm"}:
                raise ValueError(
                    "BPS --input-file requires an HTML page saved from the official "
                    "BPS source, not a CSV or spreadsheet."
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

    def parse(self, payload: bytes) -> list[RegionalVehicleStatisticInput]:
        observed_at = datetime.now(UTC)
        soup = BeautifulSoup(payload, "html.parser")
        records: dict[str, RegionalVehicleStatisticInput] = {}

        for row in soup.find_all("tr"):
            cells = [
                self._clean_cell(cell.get_text(" ", strip=True))
                for cell in row.find_all(["th", "td"])
            ]
            cells = [cell for cell in cells if cell]
            if len(cells) < 6:
                continue

            value_cells = cells[-5:]
            prefix_cells = cells[:-5]
            region = next(
                (
                    cell
                    for cell in reversed(prefix_cells)
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
                    "acquisition": "public_statistics_table",
                },
            )

        if len(records) < 10:
            raise ValueError(
                "BPS vehicle-stock table produced too few regional rows. "
                "The BPS page may render its rows with JavaScript or the table "
                "layout may have changed. Try saving the fully rendered official "
                "BPS 2025 table page as HTML and run "
                "'yarn ingest --source vehicle_stock_latest --input-file "
                "PATH_TO_FILE.html --persist-db'."
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
            r"\\s*(\\d{1,3}(?:[.,]\\d{3})*|\\d+)\\s*(?:\\*{1,3}|[era-bc])?\\s*",
            value,
            flags=re.IGNORECASE,
        )
        if match is None:
            raise ValueError(f"Invalid BPS vehicle count: {value!r}")
        return int(match.group(1).replace(".", "").replace(",", ""))
