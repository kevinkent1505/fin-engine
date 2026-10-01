from pathlib import Path

from riil_analysis.models import VehicleValuationRequest
from riil_analysis.valuation import estimate_vehicle_value


DATA_PATH = Path(__file__).parents[3] / "data" / "sample" / "vehicles.csv"


def test_avanza_jakarta_baseline() -> None:
    result = estimate_vehicle_value(
        VehicleValuationRequest(
            make="Toyota",
            model="Avanza",
            year=2023,
            region="Jakarta",
        ),
        str(DATA_PATH),
    )

    assert result.valuation.estimate == 218_000_000
    assert result.valuation.low == 202_000_000
    assert result.valuation.high == 236_000_000
    assert result.sample_size == 13
    assert result.method == "comparable_market_v1"


def test_matching_is_case_insensitive() -> None:
    result = estimate_vehicle_value(
        VehicleValuationRequest(
            make="toyota",
            model="AVANZA",
            year=2023,
            region="jakarta",
        ),
        str(DATA_PATH),
    )

    assert result.sample_size == 13
