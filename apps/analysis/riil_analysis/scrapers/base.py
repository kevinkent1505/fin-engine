from abc import ABC, abstractmethod
from pathlib import Path

from riil_analysis.ingestion.models import RawVehicleObservation


class VehicleSourceAdapter(ABC):
    source_id: str
    source_url: str

    def __init__(self) -> None:
        self.fetch_limit: int | None = None
        self.input_path: Path | None = None
        self.authorization_reference: str | None = None
        self.start_url: str | None = None
        self.request_delay_seconds: float = 2.0

    def set_fetch_limit(self, limit: int | None) -> None:
        """Allow multi-request adapters to cap network work during development."""
        self.fetch_limit = limit

    def set_input_path(self, path: Path | None) -> None:
        """Provide a local file for file-backed or licensed-feed adapters."""
        self.input_path = path

    def set_authorization_reference(self, reference: str | None) -> None:
        """Record the permission/contract/ticket authorizing restricted-source use."""
        self.authorization_reference = reference

    def set_start_url(self, url: str | None) -> None:
        """Override the adapter's default discovery URL."""
        self.start_url = url

    def set_request_delay_seconds(self, seconds: float) -> None:
        """Configure a self-imposed delay between outbound requests."""
        if seconds < 1.0:
            raise ValueError(
                "request delay must be at least 1.0 second for marketplace crawls"
            )
        self.request_delay_seconds = seconds

    @abstractmethod
    def fetch(self) -> bytes:
        """Fetch the source payload without applying analytical logic."""

    @abstractmethod
    def parse(self, payload: bytes) -> list[RawVehicleObservation]:
        """Parse source-specific payload into the common raw contract."""

    def run(self) -> list[RawVehicleObservation]:
        return self.parse(self.fetch())
