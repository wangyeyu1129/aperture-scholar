"""Narrow structural interfaces: implementations are injected at the composition root."""

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from aperture_scholar.domain.models import (
    Document,
    Extraction,
    Gap,
    GenerationContext,
    Idea,
    IdeaCard,
    NoveltyReport,
    Paper,
    Review,
)


class PaperSource(Protocol):
    def search(self, query: str, limit: int) -> Sequence[Paper]: ...


class CitationSource(Protocol):
    def expand(self, paper_ids: Sequence[str], hops: int) -> Sequence[Paper]: ...


class FullTextParser(Protocol):
    def parse(self, paper: Paper, content: bytes) -> Document: ...


class EmbeddingProvider(Protocol):
    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...


class ExtractionProvider(Protocol):
    def extract(self, document: Document, *, repair_hint: str | None = None) -> Extraction: ...


class EntityNormalizer(Protocol):
    def normalize(self, records: Sequence[Extraction]) -> Sequence[Extraction]: ...


class GapDiscovery(Protocol):
    def discover(self, records: Sequence[Extraction], as_of: date) -> Sequence[Gap]: ...


class ContextRetriever(Protocol):
    def retrieve(self, gap: Gap, limit: int) -> GenerationContext: ...


class IdeaGenerator(Protocol):
    def generate(
        self,
        gap: Gap,
        context: GenerationContext,
        excluded: Sequence[str],
        count: int,
    ) -> Sequence[Idea]: ...


class IdeaReviewer(Protocol):
    def review(self, idea: Idea, context: GenerationContext) -> Sequence[Review]: ...
    def revise(self, idea: Idea, reviews: Sequence[Review]) -> Idea: ...


class NoveltyChecker(Protocol):
    def check(self, idea: Idea) -> NoveltyReport: ...


class IdeaRanker(Protocol):
    def rank(
        self,
        ideas: Sequence[Idea],
        gaps: Sequence[Gap],
        reports: Sequence[NoveltyReport],
    ) -> Sequence[IdeaCard]: ...


class CardRepository(Protocol):
    def save(self, cards: Sequence[IdeaCard]) -> None: ...
    def list_cards(self) -> Sequence[IdeaCard]: ...


class PaperRepository(Protocol):
    def upsert(self, paper: Paper) -> None: ...
    def get(self, paper_id: str) -> Paper | None: ...


class ResponseCache(Protocol):
    def get(self, key: str) -> str | None: ...
    def put(self, key: str, payload: str, ttl_seconds: float) -> None: ...
