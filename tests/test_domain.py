import math

import pytest
from pydantic import ValidationError

from aperture_scholar.application.ranking import WeightedScore
from aperture_scholar.config import RankingWeights, Settings
from aperture_scholar.domain.errors import EvidenceRejected
from aperture_scholar.domain.evidence import EvidenceValidator
from aperture_scholar.domain.models import (
    DimensionScores,
    Evidence,
    IdeaCard,
    NoveltyReport,
    Overlap,
    Paper,
    PriorArt,
)
from aperture_scholar.domain.similarity import cosine_similarity, deduplicate_vectors


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ([1, 0], [1, 0], 1),
        ([1, 0], [0, 1], 0),
        ([1, 0], [-1, 0], -1),
        ([1e200, 0], [1e200, 0], 1),
    ],
)
def test_cosine(left, right, expected):
    assert cosine_similarity(left, right) == pytest.approx(expected)


@pytest.mark.parametrize(
    "left,right", [([], []), ([1], [1, 2]), ([0], [1]), ([math.nan], [1]), ([math.inf], [1])]
)
def test_cosine_rejects_invalid_vectors(left, right):
    with pytest.raises(ValueError):
        cosine_similarity(left, right)


def test_stable_greedy_deduplication():
    assert deduplicate_vectors([[1, 0], [1, 0], [0, 1]], 0.85) == [0, 2]
    assert deduplicate_vectors([], 0.85) == []


def test_quotation_matches_normalized_text(document, extraction):
    evidence = Evidence(paper_id="p1", section_id="lim", quote="We  lack multilingual evaluation.")
    EvidenceValidator().verify(evidence, document)
    assert EvidenceValidator().validate(extraction, document) == extraction


def test_fuzzy_typo_matches_only_high_threshold(document):
    evidence = Evidence(paper_id="p1", section_id="lim", quote="We lack multilinguai evaluation.")
    EvidenceValidator(0.95).verify(evidence, document)
    with pytest.raises(EvidenceRejected):
        EvidenceValidator(1).verify(evidence, document)


@pytest.mark.parametrize(
    "changes",
    [
        {"paper_id": "another"},
        {"section_id": "absent"},
        {"quote": "A fabricated claim about unlimited compute."},
    ],
)
def test_evidence_bound_to_declared_source(document, extraction, changes):
    evidence = extraction.limitations[0].evidence.model_copy(update=changes)
    with pytest.raises(EvidenceRejected):
        EvidenceValidator().verify(evidence, document)


def test_reviewer_claim_cannot_cite_author_section(document, extraction):
    limitation = extraction.limitations[0].model_copy(update={"source": "reviewer"})
    with pytest.raises(EvidenceRejected):
        EvidenceValidator().validate(
            extraction.model_copy(update={"limitations": (limitation,)}), document
        )


def test_weighted_score():
    assert WeightedScore(RankingWeights()).calculate(
        DimensionScores(novelty=1, feasibility=0, impact=0)
    ) == pytest.approx(0.4)
    with pytest.raises(ValidationError):
        RankingWeights(novelty=1, feasibility=1, impact=1)


def test_environment_override(monkeypatch):
    monkeypatch.setenv("APERTURE_REVIEW_ROUNDS", "0")
    monkeypatch.setenv("APERTURE_S2__REQUESTS_PER_SECOND", "0.5")
    settings = Settings(_env_file=None)
    assert settings.review_rounds == 0
    assert settings.s2.requests_per_second == 0.5


def test_models_immutable_and_strict():
    paper = Paper(id="p", title="Paper")
    with pytest.raises(ValidationError):
        paper.title = "Changed"
    with pytest.raises(ValidationError):
        Paper(id="p", title="Paper", unexpected="value")


def test_incomplete_or_overlapping_reports_are_ineligible(idea):
    assert not NoveltyReport(idea_id=idea.id, search_complete=False, queries=("q",)).eligible
    assert not NoveltyReport(idea_id=idea.id, search_complete=True, queries=()).eligible
    report = NoveltyReport(
        idea_id=idea.id,
        search_complete=True,
        queries=("q",),
        neighbors=(
            PriorArt(
                paper=Paper(id="prior", title="Prior work"),
                overlap=Overlap.HIGH,
                difference="Same core method",
                similarity=0.9,
            ),
        ),
    )
    assert not report.eligible


def test_cards_reject_wrong_provenance(card):
    payload = card.model_dump()
    payload["novelty"]["idea_id"] = "another"
    with pytest.raises(ValidationError):
        IdeaCard.model_validate(payload)
