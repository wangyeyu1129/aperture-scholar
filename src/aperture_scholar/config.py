"""Validated defaults plus environment overrides, with no credential literals."""

from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from aperture_scholar.domain.models import Model, UnitScore


class ProviderSettings(Model):
    model: str | None = None
    temperature: Annotated[float, Field(ge=0, le=2)] = 0.2


class ScholarSettings(Model):
    base_url: str = "https://api.semanticscholar.org/graph/v1/"
    api_key: SecretStr | None = None
    timeout_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 30
    requests_per_second: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 1
    max_attempts: Annotated[int, Field(ge=1, le=10)] = 3
    cache_ttl_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 86400


class RankingWeights(Model):
    novelty: UnitScore = 0.4
    feasibility: UnitScore = 0.35
    impact: UnitScore = 0.25

    @model_validator(mode="after")
    def normalized(self) -> "RankingWeights":
        if abs(self.novelty + self.feasibility + self.impact - 1) > 1e-9:
            raise ValueError("ranking weights must sum to one")
        return self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APERTURE_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="forbid",
    )
    database_path: Path = Path("var/aperture.sqlite3")
    s2: ScholarSettings = Field(default_factory=ScholarSettings)
    extraction: ProviderSettings = Field(default_factory=ProviderSettings)
    generation: ProviderSettings = Field(default_factory=lambda: ProviderSettings(temperature=0.9))
    ranking_weights: RankingWeights = Field(default_factory=RankingWeights)
    evidence_threshold: Annotated[float, Field(gt=0, le=1)] = 0.95
    entity_similarity_threshold: UnitScore = 0.85
    deduplication_threshold: UnitScore = 0.85
    novelty_similarity_threshold: UnitScore = 0.6
    extraction_attempts: Annotated[int, Field(ge=1, le=5)] = 2
    review_rounds: Annotated[int, Field(ge=0, le=10)] = 2
    swiss_rounds: Annotated[int, Field(ge=1, le=20)] = 5
    ideas_per_gap: Annotated[int, Field(ge=1, le=20)] = 5
    context_limit: Annotated[int, Field(ge=1)] = 8
    gap_limit: Annotated[int, Field(ge=1)] = 40
    output_limit: Annotated[int, Field(ge=1)] = 20
