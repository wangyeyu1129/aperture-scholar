"""Composition root: infrastructure and configuration are assembled only here."""

from aperture_scholar.application.pipeline import RecommendationPipeline
from aperture_scholar.config import Settings
from aperture_scholar.domain.errors import CapabilityNotImplemented
from aperture_scholar.infrastructure.sqlite import SQLiteDatabase


def build_database(settings: Settings) -> SQLiteDatabase:
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    return database


def build_pipeline(settings: Settings) -> RecommendationPipeline:
    """Wire implementations here when E01-R01 are ready; no implicit mock/live fallback."""
    raise CapabilityNotImplemented(
        "Live pipeline is not wired. Implement research adapters E01-R01; see docs/ROADMAP.md."
    )
