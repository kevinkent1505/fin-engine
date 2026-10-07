from dataclasses import dataclass
from typing import Literal


OfficialSourceFamily = Literal["njkb", "regional_vehicle_stock"]

FIN_ENGINE_USER_AGENT = "FinEngine/0.1 (+https://riil.id)"
INDONESIA_REGION = "Indonesia"

DEFAULT_MARKETPLACE_REQUEST_DELAY_SECONDS = 2.0
MIN_MARKETPLACE_REQUEST_DELAY_SECONDS = 1.0


@dataclass(frozen=True)
class OfficialSourceConfig:
    """One centrally managed official-public-data release."""

    source_id: str
    family: OfficialSourceFamily
    publisher: str
    source_url: str
    release_year: int
    publication_label: str
    download_url: str | None = None
    timeout_seconds: float = 30.0
    accept_header: str = "text/html,application/xhtml+xml"
    default_region: str = INDONESIA_REGION


# Historical releases remain explicit for provenance. Application code should
# normally call latest_official_source(...) or use the semantic aliases below,
# rather than depending on a year-specific source id.
OFFICIAL_SOURCES: tuple[OfficialSourceConfig, ...] = (
    OfficialSourceConfig(
        source_id="kemendagri_njkb_2025",
        family="njkb",
        publisher="Kementerian Dalam Negeri / JDIH BPK",
        source_url=(
            "https://peraturan.bpk.go.id/Details/321612/"
            "permendagri-no-7-tahun-2025"
        ),
        download_url=(
            "https://peraturan.bpk.go.id/Download/383357/"
            "Permendagri%20Nomor%207%20Tahun%202025.pdf"
        ),
        release_year=2025,
        publication_label="Permendagri No. 7 Tahun 2025",
        timeout_seconds=60.0,
        accept_header="application/pdf",
    ),
    OfficialSourceConfig(
        source_id="bps_vehicle_stock_2025",
        family="regional_vehicle_stock",
        publisher="Badan Pusat Statistik",
        source_url=(
            "https://www.bps.go.id/id/statistics-table/3/"
            "VjJ3NGRGa3dkRk5MTlU1bVNFOTVVbmQyVURSTVFUMDkjMw%3D%3D/"
            "jumlah-kendaraan-bermotor-menurut-provinsi-dan-jenis-kendaraan"
        ),
        release_year=2025,
        publication_label="BPS provincial motor-vehicle statistics, 2025",
        timeout_seconds=30.0,
    ),
)


def get_official_source(source_id: str) -> OfficialSourceConfig:
    try:
        return next(
            source for source in OFFICIAL_SOURCES if source.source_id == source_id
        )
    except StopIteration as error:
        supported = ", ".join(source.source_id for source in OFFICIAL_SOURCES)
        raise ValueError(
            f"Unknown official source {source_id!r}. Supported: {supported}"
        ) from error


def latest_official_source(
    family: OfficialSourceFamily,
) -> OfficialSourceConfig:
    candidates = [source for source in OFFICIAL_SOURCES if source.family == family]
    if not candidates:
        raise ValueError(f"No official source configured for family {family!r}.")
    return max(candidates, key=lambda source: source.release_year)


def official_source_aliases() -> dict[str, str]:
    """Stable semantic aliases for callers that should not depend on a year."""
    return {
        "njkb_latest": latest_official_source("njkb").source_id,
        "vehicle_stock_latest": latest_official_source(
            "regional_vehicle_stock"
        ).source_id,
    }


def official_refresh_source_ids() -> tuple[str, ...]:
    """The latest configured release from every official-source family."""
    return (
        latest_official_source("njkb").source_id,
        latest_official_source("regional_vehicle_stock").source_id,
    )
