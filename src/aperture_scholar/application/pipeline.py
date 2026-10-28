"""Orchestrator: stages depend on contracts; quality failures stop propagation."""

import logging
from collections.abc import Sequence
from datetime import date

from aperture_scholar.application.extraction import ExtractionService
from aperture_scholar.application.ports import (
    CardRepository,
    ContextRetriever,
    EmbeddingProvider,
    EntityNormalizer,
    GapDiscovery,
    IdeaGenerator,
    IdeaRanker,
    IdeaReviewer,
    NoveltyChecker,
)
from aperture_scholar.config import Settings
from aperture_scholar.domain.errors import QualityGateRejected
from aperture_scholar.domain.models import Document, Idea, IdeaCard, NoveltyReport
from aperture_scholar.domain.similarity import deduplicate_vectors

logger = logging.getLogger(__name__)


class RecommendationPipeline:
    def __init__(
        self,
        *,
        extraction: ExtractionService,
        normalizer: EntityNormalizer,
        gaps: GapDiscovery,
        retriever: ContextRetriever,
        generator: IdeaGenerator,
        reviewer: IdeaReviewer,
        novelty: NoveltyChecker,
        ranker: IdeaRanker,
        embeddings: EmbeddingProvider,
        cards: CardRepository,
        settings: Settings,
    ) -> None:
        self.extraction, self.normalizer, self.gaps = extraction, normalizer, gaps
        self.retriever, self.generator, self.reviewer = retriever, generator, reviewer
        self.novelty, self.ranker, self.embeddings = novelty, ranker, embeddings
        self.cards, self.settings = cards, settings

    def run(self, documents: Sequence[Document], *, as_of: date) -> list[IdeaCard]:
        """Input must already be scoped and parsed. as_of makes temporal runs explicit."""
        if not documents:
            return []
        ids = [document.paper.id for document in documents]
        if len(ids) != len(set(ids)):
            raise QualityGateRejected("duplicate document IDs")
        if any(d.paper.year is None or d.paper.year > as_of.year for d in documents):
            raise QualityGateRejected("unknown/future publication year in temporal corpus")
        records = [self.extraction.extract(document) for document in documents]
        canonical = self.normalizer.normalize(records)
        if len(canonical) != len(records) or {r.paper_id for r in canonical} != set(ids):
            raise QualityGateRejected("normalizer changed corpus provenance")
        gaps = sorted(self.gaps.discover(canonical, as_of), key=lambda g: (-g.score, g.id))
        selected = gaps[: self.settings.gap_limit]
        if len({gap.id for gap in selected}) != len(selected):
            raise QualityGateRejected("duplicate gap IDs")
        corpus_ids = set(ids)
        if any(not set(g.evidence_paper_ids) <= corpus_ids for g in selected):
            raise QualityGateRejected("gap cites a paper outside the corpus")
        ideas: list[Idea] = []
        for gap in selected:
            context = self.retriever.retrieve(gap, self.settings.context_limit)
            canonical_by_id = {record.paper_id: record for record in canonical}
            if len(context) > self.settings.context_limit or any(
                canonical_by_id.get(record.paper_id) != record for record in context
            ):
                raise QualityGateRejected("retriever returned unexpected corpus records")
            batch = self.generator.generate(
                gap,
                context,
                [idea.similarity_text() for idea in ideas],
                self.settings.ideas_per_gap,
            )
            if len(batch) > self.settings.ideas_per_gap or any(i.gap_id != gap.id for i in batch):
                raise QualityGateRejected("generator violated gap/count contract")
            for idea in batch:
                for _ in range(self.settings.review_rounds):
                    reviews = self.reviewer.review(idea, context)
                    if any(review.idea_id != idea.id for review in reviews):
                        raise QualityGateRejected("review belongs to another idea")
                    revised = self.reviewer.revise(idea, reviews)
                    if revised.id != idea.id or revised.gap_id != gap.id:
                        raise QualityGateRejected("revision changed provenance")
                    idea = revised
                ideas.append(idea)
            # Compare each new batch with the entire retained history.
            ideas = self._deduplicate(ideas)
        reports: list[NoveltyReport] = []
        eligible: list[Idea] = []
        for idea in ideas:
            report = self.novelty.check(idea)
            if report.idea_id != idea.id:
                raise QualityGateRejected("novelty report belongs to another idea")
            if report.eligible:
                eligible.append(idea)
                reports.append(report)
        ranked = list(self.ranker.rank(eligible, selected, reports)) if eligible else []
        eligible_ids = {idea.id for idea in eligible}
        if len({card.idea.id for card in ranked}) != len(ranked) or any(
            card.idea.id not in eligible_ids for card in ranked
        ):
            raise QualityGateRejected("ranker returned unexpected or duplicate ideas")
        ideas_by_id = {idea.id: idea for idea in eligible}
        gaps_by_id = {gap.id: gap for gap in selected}
        reports_by_id = {report.idea_id: report for report in reports}
        if any(
            card.idea != ideas_by_id[card.idea.id]
            or card.gap != gaps_by_id.get(card.idea.gap_id)
            or card.novelty != reports_by_id[card.idea.id]
            for card in ranked
        ):
            raise QualityGateRejected("ranker altered reviewed artifacts")
        output = ranked[: self.settings.output_limit]
        self.cards.save(output)
        logger.info("recommendation_run_completed", extra={"card_count": len(output)})
        return output

    def _deduplicate(self, ideas: list[Idea]) -> list[Idea]:
        if not ideas:
            return []
        if len({idea.id for idea in ideas}) != len(ideas):
            raise QualityGateRejected("duplicate idea IDs")
        vectors = self.embeddings.embed([idea.similarity_text() for idea in ideas])
        if len(vectors) != len(ideas):
            raise QualityGateRejected("embedding cardinality differs from idea cardinality")
        kept = deduplicate_vectors(vectors, self.settings.deduplication_threshold)
        return [ideas[index] for index in kept]
