"""Two independent gap strategies, both returning a common evidence-bearing model."""

from collections.abc import Sequence
from datetime import date

from aperture_scholar.application.ports import GapDiscovery
from aperture_scholar.domain.errors import CapabilityNotImplemented
from aperture_scholar.domain.models import Extraction, Gap


class BipartiteGapDiscovery:
    def discover(self, records: Sequence[Extraction], as_of: date) -> Sequence[Gap]:
        """TODO G01: cluster canonical entities; weighted problem-method graph.

        Rank missing links by transferability, growth and method activity. Apply a
        separate plausibility gate; a missing link is not itself a research gap.
        """
        raise CapabilityNotImplemented("G01: bipartite gaps and plausibility gate")


class LimitationGapDiscovery:
    def discover(self, records: Sequence[Extraction], as_of: date) -> Sequence[Gap]:
        """TODO G02: HDBSCAN, source weights, >= configured distinct papers, solved check."""
        raise CapabilityNotImplemented("G02: limitation clustering and solved-pain check")


class CompositeGapDiscovery:
    def __init__(self, strategies: Sequence[GapDiscovery]) -> None:
        self.strategies = tuple(strategies)

    def discover(self, records: Sequence[Extraction], as_of: date) -> Sequence[Gap]:
        """TODO G03: merge strategy outputs; semantic gap deduplication and calibration."""
        raise CapabilityNotImplemented("G03: unified gap discovery")
