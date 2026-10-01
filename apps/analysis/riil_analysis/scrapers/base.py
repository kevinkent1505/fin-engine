from abc import ABC, abstractmethod

from riil_analysis.ingestion.models import RawVehicleObservation


class VehicleSourceAdapter(ABC):
    source_id: str
    source_url: str

    def __init__(self) -> None:
        self.fetch_limit: int | None = None

    def set_fetch_limit(self, limit: int | None) -> None:
        """Allow multi-request adapters to cap network work during development."""
        self.fetch_limit = limit

    @abstractmethod
    def fetch(self) -> bytes:
        """Fetch the source payload without applying analytical logic."""

    @abstractmethod
    def parse(self, payload: bytes) -> list[RawVehicleObservation]:
        """Parse source-specific payload into the common raw contract."""

    def run(self) -> list[RawVehicleObservation]:
        return self.parse(self.fetch())
