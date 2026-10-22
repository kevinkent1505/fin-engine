"""Regional motor-vehicle statistics from BPS official source tables."""

import csv
from datetime import UTC, datetime
import hashlib
import io
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import httpx

from riil_analysis.config import (
    BPS_BROWSER_CHANNELS,
    BPS_BROWSER_TIMEOUT_SECONDS,
    BPS_MIN_LIVE_ROWS,
    FIN_ENGINE_USER_AGENT,
    latest_official_source,
)
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
        self._used_browser = False
        self._remote_csv_export = False
        self._official_export_download = None

    def set_input_path(self, path: Path | None) -> None:
        """Use an official BPS HTML or CSV export instead of a live request."""
        self.input_path = path
        self._used_browser = False
        self._remote_csv_export = False
        self._official_export_download = None

    def fetch(self) -> bytes:
        if self.input_path is not None:
            if self.input_path.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
                raise ValueError(
                    "BPS --input-file accepts a saved official BPS HTML page "
                    "(.html/.htm) or table export (.csv)."
                )
            return self.input_path.read_bytes()

        export_url = os.getenv("BPS_VEHICLE_STOCK_CSV_URL", "").strip()
        if export_url:
            parsed = urlparse(export_url)
            host = (parsed.hostname or "").lower()
            if (
                parsed.scheme != "https"
                or not host
                or not (host == "bps.go.id" or host.endswith(".bps.go.id"))
                or parsed.username is not None
                or parsed.password is not None
            ):
                raise ValueError(
                    "BPS_VEHICLE_STOCK_CSV_URL must be an HTTPS link "
                    "hosted directly on an official *.bps.go.id domain."
                )
            try:
                with httpx.Client(
                    follow_redirects=True,
                    timeout=SOURCE_CONFIG.timeout_seconds,
                    headers={"User-Agent": FIN_ENGINE_USER_AGENT},
                ) as client:
                    response = client.get(export_url)
                    response.raise_for_status()
            except httpx.HTTPError as error:
                # Avoid emitting potential private export-query parameters.
                raise ValueError(
                    f"Official BPS CSV export request failed: {type(error).__name__}. "
                    "Verify the configured BPS export URL and access rights."
                ) from error

            final_host = (response.url.host or "").lower()
            if not (
                final_host == "bps.go.id"
                or final_host.endswith(".bps.go.id")
            ):
                raise ValueError("BPS CSV export redirected off the official BPS domain.")
            if len(response.content) > 20_000_000:
                raise ValueError("BPS CSV export exceeds the 20 MB safety limit.")
            self._remote_csv_export = True
            self._official_export_download = (
                f"{response.url.scheme}://{final_host}{response.url.path}"
            )
            return response.content

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

    def fetch_rendered(self) -> bytes:
        """Load the official BPS table in a browser when HTML omits JS rows.

        This uses regular Playwright automation of the public page. It does
        not bypass authentication, challenges, or access controls.
        On Windows, the system Microsoft Edge installation is tried first.
        """
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise RuntimeError(
                "BPS renders the official table with JavaScript. "
                "Install the browser integration with 'yarn setup' "
                "(Python extra: bps_browser)."
            ) from error

        failures: list[str] = []
        with sync_playwright() as playwright:
            for channel in BPS_BROWSER_CHANNELS:
                name = channel or "bundled Chromium"
                browser = None
                try:
                    launch_options = (
                        {"channel": channel} if channel is not None else {}
                    )
                    browser = playwright.chromium.launch(
                        headless=True, **launch_options
                    )
                    page = browser.new_page(locale="id-ID")
                    page.goto(
                        self.source_url,
                        wait_until="domcontentloaded",
                        timeout=BPS_BROWSER_TIMEOUT_SECONDS * 1000,
                    )
                    page.wait_for_function(
                        """(minRows) =>
                        Array.from(document.querySelectorAll('tr')).filter(
                          row => row.querySelectorAll('td,th').length >= 6 &&
                            row.querySelectorAll('td').length >= 5
                        ).length >= minRows""",
                        arg=BPS_MIN_LIVE_ROWS,
                        timeout=BPS_BROWSER_TIMEOUT_SECONDS * 1000,
                    )

                    headings = " ".join(
                        page.locator("h1, h2").all_inner_texts()
                    )
                    if str(self.year) not in headings:
                        raise ValueError(
                            f"BPS browser page does not identify year "
                            f"{self.year} in the table heading. "
                            "Refusing to import a potentially wrong year."
                        )

                    rendered = page.content().encode("utf-8")
                    self._used_browser = True
                    return rendered
                except (PlaywrightError, ValueError) as error:
                    failures.append(
                        f"{name}: {type(error).__name__}: {error}"
                    )
                finally:
                    if browser is not None:
                        browser.close()

        raise RuntimeError(
            "BPS did not return a complete 2025 table in an ordinary "
            "browser session. Install browser binaries with "
            "'yarn setup:bps-browser' if necessary; if BPS blocks "
            "automated access, use an authorized BPS WebAPI key or "
            "the official CSV export. Browser attempts: "
            + "; ".join(failures)
        )

    def _validate_live_snapshot(
        self, records: list[RegionalVehicleStatisticInput], payload: bytes
    ) -> None:
        """Reject wrong-year, paginated, or incomplete live table data."""
        page = BeautifulSoup(payload, "html.parser")
        headings = " ".join(
            heading.get_text(" ", strip=True)
            for heading in page.find_all(["h1", "h2"])
        )
        if not self._remote_csv_export and not re.search(rf"\b{self.year}\b", headings):
            raise ValueError(
                f"BPS live page heading does not identify year {self.year}; "
                "refusing to relabel another publication."
            )

        regions = {record.region for record in records}
        required = {"Aceh", "DKI Jakarta", "Jawa Timur", "Indonesia"}
        if len(regions) < BPS_MIN_LIVE_ROWS or not required.issubset(regions):
            raise ValueError(
                f"Incomplete BPS {self.year} live table: "
                f"{len(regions)} validated regional/national rows. "
                "The website may paginate or defer JavaScript table rows."
            )

    def _input_rows(self, payload: bytes) -> list[list[str]]:
        if self._remote_csv_export or (
            self.input_path is not None and self.input_path.suffix.lower() == ".csv"
        ):
            try:
                text = payload.decode("utf-8-sig")
            except UnicodeDecodeError as error:
                raise ValueError(
                    "BPS CSV must be UTF-8. Re-export the official table as UTF-8 CSV."
                ) from error

            # BPS exports sometimes begin with one-cell title/metadata rows,
            # which causes csv.Sniffer to reject otherwise valid CSV files.
            candidates = [
                list(csv.reader(io.StringIO(text), delimiter=delimiter))
                for delimiter in (",", ";", "\t")
            ]
            rows = max(
                candidates,
                key=lambda candidate: sum(len(row) >= 6 for row in candidate),
            )
            if sum(len(row) >= 6 for row in rows) < MIN_REGIONAL_ROWS:
                raise ValueError(
                    "BPS CSV has too few tabular rows. Export the provincial "
                    "2025 vehicle-stock table in CSV format."
                )
            rows = [
                [self._clean_cell(cell) for cell in row]
                for row in rows
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
            header_lower = header_text.lower()
            if not (
                ("provinsi" in header_lower or "province" in header_lower)
                and ("kendaraan" in header_lower or "motor" in header_lower)
            ):
                raise ValueError(
                    "BPS CSV is missing province and motor-vehicle table "
                    "headings. Verify that it was exported from the official "
                    "2025 provincial vehicle-stock table."
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
        if self._remote_csv_export:
            acquisition = "official_bps_csv_export_url"
            provenance = {
                "export_url": self._official_export_download or self.source_url,
                "import_sha256": hashlib.sha256(payload).hexdigest(),
            }
        elif self.input_path is not None:
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
                    "acquisition": (
                        "public_statistics_table_browser"
                        if self._used_browser
                        else acquisition
                    ),
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
        if self.input_path is not None:
            # Explicitly supplied snapshots never trigger network requests.
            return self.parse(self.fetch())

        self._used_browser = False
        self._remote_csv_export = False
        try:
            direct_payload = self.fetch()
            direct_records = self.parse(direct_payload)
            self._validate_live_snapshot(direct_records, direct_payload)
            return direct_records
        except (ValueError, httpx.HTTPError) as direct_error:
            if self._remote_csv_export:
                raise RuntimeError(
                    "Official BPS CSV export failed validation; no incomplete "
                    "data were saved. Check source year, province coverage "
                    "and totals."
                ) from direct_error

            if isinstance(direct_error, httpx.HTTPStatusError) and (
                direct_error.response.status_code in (401, 403)
            ):
                raise RuntimeError(
                    "BPS refused automated HTTP access (HTTP "
                    f"{direct_error.response.status_code}). Do not retry "
                    "with a browser or bypass access controls. Configure "
                    "BPS_VEHICLE_STOCK_CSV_URL with an approved official "
                    "CSV export from BPS, or import its exported CSV using "
                    "yarn ingest --source vehicle_stock_latest "
                    "--input-file path/to/bps-2025.csv --persist-db. "
                    "No incomplete data were saved."
                ) from direct_error

            # The BPS HTML response usually omits JavaScript-rendered rows.
            # Retry once using an ordinary browser; never persist partial data.
            print(
                f"BPS HTTP table incomplete ({direct_error}); "
                "loading the official page in a browser...",
                file=sys.stderr,
            )
            try:
                browser_payload = self.fetch_rendered()
                rendered_records = self.parse(browser_payload)
                self._validate_live_snapshot(rendered_records, browser_payload)
                return rendered_records
            except Exception as browser_error:
                raise RuntimeError(
                    "Automatic BPS refresh failed: the HTTP table was "
                    f"unavailable/incomplete ({direct_error}); browser "
                    f"fallback also failed ({browser_error}). "
                    "No incomplete data were saved."
                ) from browser_error

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
