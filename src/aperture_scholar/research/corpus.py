"""Corpus use cases to implement after the foundational contracts are stable."""

from collections.abc import Sequence
from datetime import date

from aperture_scholar.domain.errors import CapabilityNotImplemented
from aperture_scholar.domain.models import Paper


class CorpusBuilder:
    def build(self, seeds: Sequence[str], query: str, *, as_of: date) -> Sequence[Paper]:
        """TODO C01: citation hops, year/keyword scope, embedding seed filter, stable IDs."""
        raise CapabilityNotImplemented("C01: seed-based corpus construction")

    def update(self, since: date, query: str) -> Sequence[Paper]:
        """TODO C02: arXiv incremental ingestion with persisted cursor and idempotency."""
        raise CapabilityNotImplemented("C02: incremental corpus update")
