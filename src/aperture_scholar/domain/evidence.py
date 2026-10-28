"""Verify quotations against the declared document and section."""

import re
import unicodedata
from difflib import SequenceMatcher

from aperture_scholar.domain.errors import EvidenceRejected
from aperture_scholar.domain.models import Document, Evidence, Extraction, LimitationSource


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip().casefold()


class EvidenceValidator:
    """Exact normalized match first; conservative equal-length fuzzy windows second."""

    def __init__(self, threshold: float = 0.95) -> None:
        if not 0 < threshold <= 1:
            raise ValueError("evidence threshold must be in (0, 1]")
        self.threshold = threshold

    def verify(self, evidence: Evidence, document: Document) -> None:
        if evidence.paper_id != document.paper.id:
            raise EvidenceRejected("quotation belongs to a different paper")
        section = next((s for s in document.sections if s.id == evidence.section_id), None)
        if section is None:
            raise EvidenceRejected("declared section is missing")
        quote, text = normalize_text(evidence.quote), normalize_text(section.text)
        if len(quote) < 8:
            raise EvidenceRejected("quotation contains too little verifiable text")
        if quote in text:
            return
        matcher = SequenceMatcher(None, quote, text, autojunk=False)
        starts = {
            max(0, block.b - block.a) for block in matcher.get_matching_blocks() if block.size
        }
        score = max(
            (
                SequenceMatcher(None, quote, text[s : s + len(quote)], autojunk=False).ratio()
                for s in starts
            ),
            default=0.0,
        )
        if score < self.threshold:
            raise EvidenceRejected("quotation does not match the declared section")

    def validate(self, extraction: Extraction, document: Document) -> Extraction:
        """Reject the artifact atomically so downstream graphs never consume bad claims."""
        if extraction.paper_id != document.paper.id:
            raise EvidenceRejected("extraction belongs to a different paper")
        sections = {s.id: s for s in document.sections}
        for limitation in extraction.limitations:
            self.verify(limitation.evidence, document)
            expected = "review" if limitation.source == LimitationSource.REVIEWER else "paper"
            if sections[limitation.evidence.section_id].source != expected:
                raise EvidenceRejected("limitation source does not agree with source document")
        for claim in extraction.future_work:
            self.verify(claim.evidence, document)
        return extraction
