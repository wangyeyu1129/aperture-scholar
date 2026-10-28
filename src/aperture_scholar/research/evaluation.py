"""Evaluation entry points, separate from the production recommendation pipeline."""

from collections.abc import Sequence
from datetime import date

from aperture_scholar.domain.errors import CapabilityNotImplemented
from aperture_scholar.domain.models import IdeaCard


class TemporalBacktest:
    def evaluate(self, cutoff: date, horizon: date) -> dict[str, float]:
        """TODO V01: freeze corpus and all retrieval snapshots; prevent temporal leakage."""
        raise CapabilityNotImplemented("V01: leakage-controlled retrospective evaluation")


class BlindReviewExporter:
    def export(self, cards: Sequence[IdeaCard], random_seed: int) -> str:
        """TODO V02: blinded, randomized system/baseline proposals with private mapping."""
        raise CapabilityNotImplemented("V02: blind human review export")


class AblationRunner:
    def run(self, variants: Sequence[str], cutoff: date) -> dict[str, dict[str, float]]:
        """TODO V03: same corpus snapshot/budget; gap/review/novelty ablations."""
        raise CapabilityNotImplemented("V03: controlled ablation runner")
