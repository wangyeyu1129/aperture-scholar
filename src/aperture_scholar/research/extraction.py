"""Vendor-neutral extension points for full-text extraction and entity resolution."""

from collections.abc import Sequence

from aperture_scholar.domain.errors import CapabilityNotImplemented
from aperture_scholar.domain.models import Document, Extraction, Paper


class GrobidParser:
    def parse(self, paper: Paper, content: bytes) -> Document:
        """TODO E01: PDF -> TEI sections; retain stable section IDs for evidence."""
        raise CapabilityNotImplemented("E01: GROBID parser adapter")


class StructuredExtractor:
    def extract(self, document: Document, *, repair_hint: str | None = None) -> Extraction:
        """TODO E02: selected sections -> validated schema; methods fallback to full text."""
        raise CapabilityNotImplemented("E02: structured LLM extraction adapter")


class SemanticEntityNormalizer:
    def normalize(self, records: Sequence[Extraction]) -> Sequence[Extraction]:
        """TODO E03: embedding candidates + synonym judge + persisted alias registry.

        Preserve paper/evidence IDs. Do not merge entities by similarity alone.
        """
        raise CapabilityNotImplemented("E03: canonical entity resolution")
