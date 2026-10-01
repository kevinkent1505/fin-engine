from collections.abc import Callable

from riil_analysis.scrapers.base import VehicleSourceAdapter
from riil_analysis.scrapers.sources.kemendagri_njkb_2025 import (
    KemendagriNjkb2025Adapter,
)


SOURCE_FACTORIES: dict[str, Callable[[], VehicleSourceAdapter]] = {
    KemendagriNjkb2025Adapter.source_id: KemendagriNjkb2025Adapter,
}


def get_source_adapter(source_id: str) -> VehicleSourceAdapter:
    try:
        return SOURCE_FACTORIES[source_id]()
    except KeyError as error:
        supported = ", ".join(sorted(SOURCE_FACTORIES))
        raise ValueError(
            f"Unknown source {source_id!r}. Supported: {supported}"
        ) from error
