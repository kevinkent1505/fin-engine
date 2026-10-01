from collections.abc import Callable

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
from riil_analysis.scrapers.sources.djp_vehicle_auction_limits import (
    DjpVehicleAuctionLimitsAdapter,
)
from riil_analysis.scrapers.sources.kemendagri_njkb_2025 import (
    KemendagriNjkb2025Adapter,
)


SOURCE_FACTORIES: dict[str, Callable[[], VehicleSourceAdapter]] = {
    CarmudiAuthorizedCrawler.source_id: CarmudiAuthorizedCrawler,
    CarmudiAuthorizedFeedAdapter.source_id: CarmudiAuthorizedFeedAdapter,
    DjpVehicleAuctionLimitsAdapter.source_id: DjpVehicleAuctionLimitsAdapter,
    KemendagriNjkb2025Adapter.source_id: KemendagriNjkb2025Adapter,
    Mobil123AuthorizedCrawler.source_id: Mobil123AuthorizedCrawler,
    Mobil123AuthorizedFeedAdapter.source_id: Mobil123AuthorizedFeedAdapter,
    OlxAuthorizedCrawler.source_id: OlxAuthorizedCrawler,
    OlxAuthorizedFeedAdapter.source_id: OlxAuthorizedFeedAdapter,
}


def get_source_adapter(source_id: str) -> VehicleSourceAdapter:
    try:
        return SOURCE_FACTORIES[source_id]()
    except KeyError as error:
        supported = ", ".join(sorted(SOURCE_FACTORIES))
        raise ValueError(
            f"Unknown source {source_id!r}. Supported: {supported}"
        ) from error
