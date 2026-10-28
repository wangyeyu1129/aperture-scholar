"""Pairwise judgment and independent tournaments per ranking dimension."""

from collections.abc import Sequence

from aperture_scholar.domain.errors import CapabilityNotImplemented
from aperture_scholar.domain.models import Gap, Idea, IdeaCard, NoveltyReport


class SwissTournamentRanker:
    def rank(
        self,
        ideas: Sequence[Idea],
        gaps: Sequence[Gap],
        reports: Sequence[NoveltyReport],
    ) -> Sequence[IdeaCard]:
        """TODO R01: pair by standings, avoid repeats, balance byes, randomize judge order.

        Run novelty, feasibility and impact independently; use WeightedScore only after
        normalizing tournament results. Specify deterministic tie breaks and persist
        comparison evidence. Never ask an LLM for absolute 1-10 scores.
        """
        raise CapabilityNotImplemented("R01: pairwise Swiss tournaments")
