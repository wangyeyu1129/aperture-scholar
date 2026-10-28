"""Evidence-based novelty pipeline. Empty search is never automatic novelty."""

from aperture_scholar.domain.errors import CapabilityNotImplemented
from aperture_scholar.domain.models import Idea, NoveltyReport


class ThreeLayerNoveltyChecker:
    def check(self, idea: Idea) -> NoveltyReport:
        """TODO N01: multi-query search + recommendations, embedding screen, semantic judge.

        Persist queries, nearest papers, overlap and differences. Bound reformulations.
        Failed/incomplete searches must return search_complete=False or raise a provider
        error; never translate a timeout into a novelty approval.
        """
        raise CapabilityNotImplemented("N01: evidence-based three-layer novelty screening")
