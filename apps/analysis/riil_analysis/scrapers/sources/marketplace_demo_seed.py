from datetime import UTC, datetime
import json

from riil_analysis.ingestion.models import RawVehicleObservation
from riil_analysis.scrapers.base import VehicleSourceAdapter


DEMO_LISTING_SOURCE = "marketplace_demo_seed"
DEMO_GENERATOR = "marketplace_demo_v1"
DEMO_REGION = "Jakarta"

# Deliberately synthetic asking-price anchors for the POC. These are not
# scraped prices, transaction prices, or claims about current market value.
DEMO_VEHICLES = [
    ("Toyota", "Avanza", "1.5 G CVT", 2023, 220_000_000),
    ("Toyota", "Avanza", "1.5 G CVT", 2024, 235_000_000),
    ("Toyota", "Avanza", "1.5 G CVT", 2025, 250_000_000),
    ("Toyota", "Fortuner", "2.4 VRZ AT", 2023, 555_000_000),
    ("Toyota", "Fortuner", "2.4 VRZ AT", 2024, 590_000_000),
    ("Toyota", "Fortuner", "2.4 VRZ AT", 2025, 625_000_000),
    ("Honda", "Brio", "RS CVT", 2023, 205_000_000),
    ("Honda", "Brio", "RS CVT", 2024, 220_000_000),
    ("Honda", "Brio", "RS CVT", 2025, 235_000_000),
    ("Honda", "HR-V", "SE CVT", 2023, 390_000_000),
    ("Honda", "HR-V", "SE CVT", 2024, 415_000_000),
    ("Honda", "HR-V", "SE CVT", 2025, 440_000_000),
    ("Mitsubishi", "Xpander", "Ultimate CVT", 2023, 285_000_000),
    ("Mitsubishi", "Xpander", "Ultimate CVT", 2024, 305_000_000),
    ("Mitsubishi", "Xpander", "Ultimate CVT", 2025, 325_000_000),
    ("Daihatsu", "Terios", "R AT", 2023, 245_000_000),
    ("Daihatsu", "Terios", "R AT", 2024, 260_000_000),
    ("Daihatsu", "Terios", "R AT", 2025, 275_000_000),
    ("Suzuki", "Ertiga", "GX AT", 2023, 235_000_000),
    ("Suzuki", "Ertiga", "GX AT", 2024, 250_000_000),
    ("Suzuki", "Ertiga", "GX AT", 2025, 265_000_000),
    ("Hyundai", "Creta", "Prime IVT", 2023, 365_000_000),
    ("Hyundai", "Creta", "Prime IVT", 2024, 390_000_000),
    ("Hyundai", "Creta", "Prime IVT", 2025, 415_000_000),
]

PRICE_OFFSETS = (-0.09, -0.07, -0.05, -0.03, -0.01, 0.0, 0.01, 0.03, 0.05, 0.07)


class MarketplaceDemoSeedAdapter(VehicleSourceAdapter):
    """Generate clearly-labelled synthetic marketplace listings for the POC."""

    source_id = DEMO_LISTING_SOURCE
    source_url = "https://example.invalid/riil-marketplace-demo"

    def fetch(self) -> bytes:
        observed_at = datetime.now(UTC).isoformat()
        rows: list[dict[str, object]] = []

        for make, model, variant, year, base_price in DEMO_VEHICLES:
            slug = f"{make}-{model}-{year}".lower().replace(" ", "-")
            for index, offset in enumerate(PRICE_OFFSETS, start=1):
                price = round(base_price * (1 + offset) / 1_000_000) * 1_000_000
                rows.append(
                    {
                        "listing_id": f"demo-{slug}-{index:02d}",
                        "listing_url": f"{self.source_url}#{slug}-{index:02d}",
                        "make": make,
                        "model": model,
                        "variant": variant,
                        "year": year,
                        "price": price,
                        "region": DEMO_REGION,
                        "observed_at": observed_at,
                    }
                )

        if self.fetch_limit is not None:
            rows = rows[: self.fetch_limit]

        return json.dumps(rows).encode("utf-8")

    def parse(self, payload: bytes) -> list[RawVehicleObservation]:
        rows = json.loads(payload.decode("utf-8"))
        records: list[RawVehicleObservation] = []

        for row in rows:
            observed_at = datetime.fromisoformat(str(row["observed_at"]))
            model = str(row["model"])
            variant = str(row["variant"])

            records.append(
                RawVehicleObservation(
                    source=self.source_id,
                    source_record_id=str(row["listing_id"]),
                    source_url=str(row["listing_url"]),
                    observed_at=observed_at,
                    make_raw=str(row["make"]),
                    model_raw=model,
                    variant_raw=variant,
                    type_raw=f"{model} {variant}",
                    year_raw=int(row["year"]),
                    region_raw=str(row["region"]),
                    price_raw=int(row["price"]),
                    price_kind="listing",
                    currency="IDR",
                    category_raw="SYNTHETIC MARKETPLACE LISTING",
                    metadata={
                        "synthetic": True,
                        "purpose": "POC demonstration",
                        "generator": DEMO_GENERATOR,
                        "access_basis": "synthetic_demo",
                        "not_real_marketplace_observation": True,
                    },
                )
            )

        return records
