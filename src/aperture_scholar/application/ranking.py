"""Only aggregate comparison-derived dimension scores here; no LLM absolute scores."""

from aperture_scholar.config import RankingWeights
from aperture_scholar.domain.models import DimensionScores


class WeightedScore:
    def __init__(self, weights: RankingWeights) -> None:
        self.weights = weights

    def calculate(self, scores: DimensionScores) -> float:
        return (
            scores.novelty * self.weights.novelty
            + scores.feasibility * self.weights.feasibility
            + scores.impact * self.weights.impact
        )
