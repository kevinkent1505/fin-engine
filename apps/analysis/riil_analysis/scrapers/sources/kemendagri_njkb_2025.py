"""Backward-compatible import for the former year-specific adapter path."""

from riil_analysis.scrapers.sources.kemendagri_njkb import KemendagriNjkbAdapter

KemendagriNjkb2025Adapter = KemendagriNjkbAdapter

__all__ = ["KemendagriNjkb2025Adapter"]
