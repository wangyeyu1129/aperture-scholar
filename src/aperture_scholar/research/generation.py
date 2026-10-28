"""Research generation contracts; prompts and provider selection remain replaceable."""

from collections.abc import Sequence

from aperture_scholar.domain.errors import CapabilityNotImplemented
from aperture_scholar.domain.models import Extraction, Gap, Idea, Review


class RetrievalContext:
    def retrieve(self, gap: Gap, limit: int) -> Sequence[Extraction]:
        """TODO I01: retrieve abstracts/limitations and canonical graph neighbors."""
        raise CapabilityNotImplemented("I01: gap-conditioned retrieval")


class ProposalGenerator:
    def generate(
        self,
        gap: Gap,
        context: Sequence[Extraction],
        excluded: Sequence[str],
        count: int,
    ) -> Sequence[Idea]:
        """TODO I02: structured proposals with experimental plan, risks and lineage."""
        raise CapabilityNotImplemented("I02: proposal generation")


class CriteriaReviewer:
    def review(self, idea: Idea, context: Sequence[Extraction]) -> Sequence[Review]:
        """TODO I03: independent novelty/feasibility/clarity criteria, versioned prompts."""
        raise CapabilityNotImplemented("I03: criterion-based reviews")

    def revise(self, idea: Idea, reviews: Sequence[Review]) -> Idea:
        """TODO I04: bounded revision preserving original idea and gap IDs."""
        raise CapabilityNotImplemented("I04: proposal revision")
