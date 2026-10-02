from datetime import UTC, datetime
import re

from bs4 import BeautifulSoup
import httpx

from riil_analysis.regional import RegionalVehicleStatisticInput


class BpsVehicleStock2025Adapter:
    """Fetch the official BPS 2025 provincial motor-vehicle statistics table."""

    source_id = "bps_vehicle_stock_2025"
    source_url = (
        "https://www.bps.go.id/id/statistics-table/3/"
        "VjJ3NGRGa3dkRk5MTlU1bVNFOTVVbmQyVURSTVFUMDkjMw%3D%3D/"
        "jumlah-kendaraan-bermotor-menurut-provinsi-dan-jenis-kendaraan"
    )
    year = 2025

    def fetch(self) -> bytes:
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

            # The official table's five rightmost data columns are passenger
            # cars, buses, trucks, motorcycles, and total vehicles. Choosing
            # the last textual prefix cell also tolerates an optional row-number
            # column before the province name.
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
                # Header rows and non-data rows naturally land here.
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
                    "publisher": "Badan Pusat Statistik",
                    "table_year": self.year,
                    "reference_type": "official_regional_vehicle_stock",
                    "acquisition": "public_statistics_table",
                },
            )

        if len(records) < 10:
            raise ValueError(
                "BPS vehicle-stock table produced too few regional rows. "
                "The public table layout may have changed."
            )

        return list(records.values())

    def run(self) -> list[RegionalVehicleStatisticInput]:
        return self.parse(self.fetch())

    @staticmethod
    def _clean_cell(value: str) -> str:
        return " ".join(value.replace("\xa0", " ").split()).strip()

    @staticmethod
    def _parse_count(value: str) -> int:
        # BPS displays Indonesian thousands separators and may append symbols
        # such as * or r. Vehicle counts are integer units, so retain digits.
        digits = re.sub(r"[^0-9]", "", value)
        if not digits:
            raise ValueError(f"Invalid BPS vehicle count: {value!r}")
        return int(digits)
