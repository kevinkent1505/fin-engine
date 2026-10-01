from datetime import UTC, datetime
import csv
import io
from pathlib import Path

from riil_analysis.ingestion.models import RawVehicleObservation
from riil_analysis.scrapers.base import VehicleSourceAdapter


REQUIRED_COLUMNS = {
    "listing_id",
    "listing_url",
    "make",
    "model",
    "year",
    "price",
    "region",
}


class AuthorizedMarketplaceCsvAdapter(VehicleSourceAdapter):
    """
    Base adapter for marketplace data obtained under an explicit license,
    partnership, API/feed agreement, or other written permission.

    This class deliberately does not crawl marketplace websites.
    """

    provider_name: str

    def fetch(self) -> bytes:
        if self.input_path is None:
            raise ValueError(
                f"{self.source_id} requires --input-file pointing to an "
                "authorized marketplace CSV export."
            )

        if not self.authorization_reference:
            raise ValueError(
                f"{self.source_id} requires --authorization-ref documenting "
                "the permission, contract, API/feed agreement, or ticket "
                "authorizing this data use."
            )

        path = Path(self.input_path)
        if not path.exists():
            raise FileNotFoundError(f"Authorized feed file not found: {path}")

        return path.read_bytes()

    def parse(self, payload: bytes) -> list[RawVehicleObservation]:
        text = payload.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        fieldnames = set(reader.fieldnames or [])

        missing = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing:
            raise ValueError(
                "Authorized marketplace feed is missing required columns: "
                + ", ".join(missing)
            )

        records: list[RawVehicleObservation] = []
        ingested_at = datetime.now(UTC)

        for row_number, row in enumerate(reader, start=2):
            listing_id = self._value(row, "listing_id")
            listing_url = self._value(row, "listing_url")
            make = self._value(row, "make")
            model = self._value(row, "model")
            year = self._value(row, "year")
            price = self._value(row, "price")
            region = self._value(row, "region")

            if not all(
                [listing_id, listing_url, make, model, year, price, region]
            ):
                continue

            variant = self._value(row, "variant")
            observed_at = self._parse_observed_at(
                self._value(row, "observed_at"),
                fallback=ingested_at,
            )

            metadata: dict[str, object] = {
                "provider": self.provider_name,
                "access_basis": "authorized_feed",
                "authorization_reference": self.authorization_reference,
                "feed_row_number": row_number,
            }

            for field in (
                "mileage_km",
                "transmission",
                "fuel",
                "seller_type",
            ):
                value = self._value(row, field)
                if value is not None:
                    metadata[field] = self._normalize_metadata_value(
                        field,
                        value,
                    )

            type_name = model
            if variant:
                type_name = f"{model} {variant}"

            records.append(
                RawVehicleObservation(
                    source=self.source_id,
                    source_record_id=listing_id,
                    source_url=listing_url,
                    observed_at=observed_at,
                    make_raw=make,
                    model_raw=model,
                    variant_raw=variant,
                    type_raw=type_name,
                    year_raw=year,
                    region_raw=region,
                    price_raw=price,
                    price_kind="listing",
                    currency=(self._value(row, "currency") or "IDR"),
                    category_raw="MARKETPLACE LISTING",
                    metadata=metadata,
                )
            )

        if not records:
            raise ValueError(
                "No usable vehicle listing rows were found in the "
                "authorized marketplace feed."
            )

        return records

    @staticmethod
    def _value(row: dict[str, str | None], key: str) -> str | None:
        value = row.get(key)
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None

    @staticmethod
    def _parse_observed_at(
        value: str | None,
        *,
        fallback: datetime,
    ) -> datetime:
        if value is None:
            return fallback

        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as error:
            raise ValueError(
                f"Invalid observed_at timestamp: {value!r}"
            ) from error

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)

        return parsed.astimezone(UTC)

    @staticmethod
    def _normalize_metadata_value(field: str, value: str) -> object:
        if field == "mileage_km":
            digits = "".join(character for character in value if character.isdigit())
            if digits:
                return int(digits)
        return value


class OlxAuthorizedFeedAdapter(AuthorizedMarketplaceCsvAdapter):
    source_id = "olx_authorized_feed"
    source_url = "https://www.olx.co.id/"
    provider_name = "OLX Indonesia"


class Mobil123AuthorizedFeedAdapter(AuthorizedMarketplaceCsvAdapter):
    source_id = "mobil123_authorized_feed"
    source_url = "https://www.mobil123.com/"
    provider_name = "Mobil123"


class CarmudiAuthorizedFeedAdapter(AuthorizedMarketplaceCsvAdapter):
    source_id = "carmudi_authorized_feed"
    source_url = "https://www.carmudi.co.id/"
    provider_name = "Carmudi Indonesia"
