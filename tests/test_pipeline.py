from datetime import date
from unittest.mock import Mock

import pytest

from aperture_scholar.application.extraction import ExtractionService
from aperture_scholar.application.pipeline import RecommendationPipeline
from aperture_scholar.config import Settings
from aperture_scholar.domain.errors import EvidenceRejected, QualityGateRejected
from aperture_scholar.domain.evidence import EvidenceValidator
from aperture_scholar.domain.models import ContextPaper, GenerationContext


@pytest.fixture
def pipeline(document, extraction, gap, idea, report, card):
    return RecommendationPipeline(
        extraction=ExtractionService(
            Mock(extract=Mock(return_value=extraction)), EvidenceValidator(), 2
        ),
        normalizer=Mock(normalize=Mock(side_effect=lambda records: records)),
        gaps=Mock(discover=Mock(return_value=[gap])),
        retriever=Mock(
            retrieve=Mock(
                return_value=GenerationContext(
                    papers=(ContextPaper(paper=document.paper, extraction=extraction),),
                )
            )
        ),
        generator=Mock(generate=Mock(return_value=[idea])),
        reviewer=Mock(
            review=Mock(return_value=[]), revise=Mock(side_effect=lambda idea, reviews: idea)
        ),
        novelty=Mock(check=Mock(return_value=report)),
        ranker=Mock(rank=Mock(return_value=[card])),
        embeddings=Mock(embed=Mock(return_value=[[1, 0]])),
        cards=Mock(),
        settings=Settings(_env_file=None),
    )


def test_pipeline_runs_and_persists(pipeline, document, card):
    assert pipeline.run([document], as_of=date(2024, 12, 31)) == [card]
    pipeline.cards.save.assert_called_once_with([card])
    assert pipeline.reviewer.review.call_count == 2
    context = pipeline.generator.generate.call_args.args[1]
    assert context.papers[0].paper == document.paper


def test_empty_corpus_does_not_call_providers(pipeline):
    assert pipeline.run([], as_of=date(2024, 12, 31)) == []
    pipeline.generator.generate.assert_not_called()


def test_future_corpus_rejected(pipeline, document):
    with pytest.raises(QualityGateRejected):
        pipeline.run([document], as_of=date(2023, 12, 31))
    pipeline.generator.generate.assert_not_called()


def test_incomplete_novelty_does_not_reach_ranker(pipeline, document, report):
    pipeline.novelty.check.return_value = report.model_copy(update={"search_complete": False})
    assert pipeline.run([document], as_of=date(2024, 12, 31)) == []
    pipeline.ranker.rank.assert_not_called()


def test_invalid_gap_citation_rejected(pipeline, document, gap):
    pipeline.gaps.discover.return_value = [
        gap.model_copy(update={"evidence_paper_ids": ("missing",)})
    ]
    with pytest.raises(QualityGateRejected):
        pipeline.run([document], as_of=date(2024, 12, 31))
    pipeline.cards.save.assert_not_called()


def test_duplicate_ideas_rejected(pipeline, document, idea):
    pipeline.generator.generate.return_value = [idea, idea]
    with pytest.raises(QualityGateRejected):
        pipeline.run([document], as_of=date(2024, 12, 31))


def test_embedding_cardinality_rejected(pipeline, document):
    pipeline.embeddings.embed.return_value = []
    with pytest.raises(QualityGateRejected):
        pipeline.run([document], as_of=date(2024, 12, 31))


def test_bad_extraction_retries_once_then_stops(document, extraction):
    provider = Mock(extract=Mock(return_value=extraction))
    validator = Mock(validate=Mock(side_effect=EvidenceRejected("bad evidence")))
    service = ExtractionService(provider, validator, 2)
    with pytest.raises(EvidenceRejected):
        service.extract(document)
    assert provider.extract.call_count == 2
    assert provider.extract.call_args.kwargs["repair_hint"]


def test_extraction_retry_can_recover(document, extraction):
    provider = Mock(extract=Mock(return_value=extraction))
    validator = Mock(validate=Mock(side_effect=[EvidenceRejected("bad"), extraction]))
    assert ExtractionService(provider, validator, 2).extract(document) == extraction


def test_normalizer_cannot_drop_records(pipeline, document):
    pipeline.normalizer.normalize.side_effect = None
    pipeline.normalizer.normalize.return_value = []
    with pytest.raises(QualityGateRejected):
        pipeline.run([document], as_of=date(2024, 12, 31))


def test_retriever_cannot_inject_future_papers(pipeline, document, extraction):
    changed_paper = document.paper.model_copy(update={"abstract": "Injected abstract"})
    pipeline.retriever.retrieve.return_value = GenerationContext(
        papers=(ContextPaper(paper=changed_paper, extraction=extraction),),
    )
    with pytest.raises(QualityGateRejected):
        pipeline.run([document], as_of=date(2024, 12, 31))


def test_ranker_cannot_change_reviewed_idea(pipeline, document, card):
    modified = card.idea.model_copy(update={"title": "Unreviewed replacement"})
    pipeline.ranker.rank.return_value = [card.model_copy(update={"idea": modified})]
    with pytest.raises(QualityGateRejected):
        pipeline.run([document], as_of=date(2024, 12, 31))
    pipeline.cards.save.assert_not_called()
