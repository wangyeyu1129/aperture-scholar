"""Bounded extraction/validation retry, independent of any LLM vendor."""

from pydantic import ValidationError

from aperture_scholar.application.ports import ExtractionProvider
from aperture_scholar.domain.errors import EvidenceRejected
from aperture_scholar.domain.evidence import EvidenceValidator
from aperture_scholar.domain.models import Document, Extraction


class ExtractionService:
    def __init__(
        self,
        provider: ExtractionProvider,
        validator: EvidenceValidator,
        attempts: int,
    ) -> None:
        if attempts < 1:
            raise ValueError("attempts must be positive")
        self.provider, self.validator, self.attempts = provider, validator, attempts

    def extract(self, document: Document) -> Extraction:
        hint: str | None = None
        for attempt in range(self.attempts):
            try:
                result = self.provider.extract(document, repair_hint=hint)
                return self.validator.validate(result, document)
            except (ValidationError, EvidenceRejected) as error:
                if attempt + 1 == self.attempts:
                    raise
                hint = type(error).__name__ + ": repair invalid fields using only supplied evidence"
        raise AssertionError("unreachable")
