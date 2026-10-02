from collections.abc import Callable
from typing import Any

from riil_analysis.scrapers.base import VehicleSourceAdapter
from riil_analysis.scrapers.sources.authorized_marketplace_crawl import (
    CarmudiAuthorizedCrawler,
    Mobil123AuthorizedCrawler,
    OlxAuthorizedCrawler,
)
from riil_analysis.scrapers.sources.authorized_marketplace_csv import (
    CarmudiAuthorizedFeedAdapter,
    Mobil123AuthorizedFeedAdapter,
    OlxAuthorizedFeedAdapter,
)
from riil_analysis.scrapers.sources.bps_vehicle_stock_2025 import (
    BpsVehicleStock2025Adapter,
)
from riil_analysis.scrapers.sources.djp_vehicle_auction_limits import (
    DjpVehicleAuctionLimitsAdapter,
)
from riil_analysis.scrapers.sources.kemendagri_njkb_2025 import (
    KemendagriNjkb2025Adapter,
)
from riil_analysis.scrapers.sources.marketplace_demo_seed import (
    MarketplaceDemoSeedAdapter,
)


SOURCE_FACTORIES: dict[str, Callable[[], VehicleSourceAdapter]] = {
    CarmudiAuthorizedCrawler.source_id: CarmudiAuthorizedCrawler,
    CarmudiAuthorizedFeedAdapter.source_id: CarmudiAuthorizedFeedAdapter,
    DjpVehicleAuctionLimitsAdapter.source_id: DjpVehicleAuctionLimitsAdapter,
    KemendagriNjkb2025Adapter.source_id: KemendagriNjkb2025Adapter,
    MarketplaceDemoSeedAdapter.source_id: MarketplaceDemoSeedAdapter,
    Mobil123AuthorizedCrawler.source_id: Mobil123AuthorizedCrawler,
    Mobil123AuthorizedFeedAdapter.source_id: Mobil123AuthorizedFeedAdapter,
    OlxAuthorizedCrawler.source_id: OlxAuthorizedCrawler,
    OlxAuthorizedFeedAdapter.source_id: OlxAuthorizedFeedAdapter,
}

REGIONAL_SOURCE_FACTORIES: dict[str, Callable[[], Any]] = {
    BpsVehicleStock2025Adapter.source_id: BpsVehicleStock2025Adapter,
}

ALL_SOURCE_IDS = sorted(set(SOURCE_FACTORIES) | set(REGIONAL_SOURCE_FACTORIES))


def get_source_adapter(source_id: str) -> VehicleSourceAdapter:
    try:
        return SOURCE_FACTORIES[source_id]()
    except KeyError as error:
        supported = ", ".join(sorted(SOURCE_FACTORIES))
        raise ValueError(
            f"Unknown vehicle source {source_id!r}. Supported: {supported}"
        ) from error


def get_regional_source_adapter(source_id: str) -> Any:
    try:
        return REGIONAL_SOURCE_FACTORIES[source_id]()
    except KeyError as error:
        supported = ", ".join(sorted(REGIONAL_SOURCE_FACTORIES))
        raise ValueError(
            f"Unknown regional source {source_id!r}. Supported: {supported}"
        ) from error
