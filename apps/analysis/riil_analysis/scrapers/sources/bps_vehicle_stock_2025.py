"""Backward-compatible import for the former year-specific adapter path."""

from riil_analysis.scrapers.sources.bps_vehicle_stock import BpsVehicleStockAdapter

BpsVehicleStock2025Adapter = BpsVehicleStockAdapter

__all__ = ["BpsVehicleStock2025Adapter"]
