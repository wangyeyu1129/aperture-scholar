import pytest

from aperture_scholar.domain.models import (
    DimensionScores,
    Document,
    Evidence,
    ExperimentPlan,
    Extraction,
    Gap,
    Idea,
    IdeaCard,
    Limitation,
    LimitationSource,
    Method,
    NoveltyReport,
    Paper,
    Problem,
    Section,
)


@pytest.fixture
def document():
    return Document(
        paper=Paper(id="p1", title="Example Paper", year=2024),
        sections=(
            Section(id="lim", heading="Limitations", text="We lack multilingual evaluation."),
        ),
    )


@pytest.fixture
def extraction(document):
    return Extraction(
        paper_id=document.paper.id,
        problem=Problem(statement="Robust retrieval", canonical="retrieval"),
        methods=(Method(name="RAG", category="retrieval", mechanism="Retrieve then generate"),),
        limitations=(
            Limitation(
                text="Limited evaluation",
                source=LimitationSource.AUTHOR,
                evidence=Evidence(
                    paper_id="p1", section_id="lim", quote="We lack multilingual evaluation."
                ),
            ),
        ),
        task_domain="NLP",
        contribution_type="new method",
    )


@pytest.fixture
def gap():
    return Gap(
        id="g1",
        kind="pain_point",
        description="Multilingual robustness",
        evidence_paper_ids=("p1",),
        score=0.8,
    )


@pytest.fixture
def idea(gap):
    return Idea(
        id="i1",
        gap_id=gap.id,
        title="Synthetic test proposal",
        problem="Evaluate language transfer",
        method_steps=("Build a multilingual retrieval baseline",),
        experiment=ExperimentPlan(
            datasets=("synthetic",), baselines=("BM25",), metrics=("Recall",)
        ),
        expected_contributions=("An evaluation protocol",),
        risks=("Dataset access",),
    )


@pytest.fixture
def report(idea):
    return NoveltyReport(
        idea_id=idea.id, search_complete=True, queries=("test multilingual transfer",)
    )


@pytest.fixture
def card(idea, gap, report):
    return IdeaCard(
        idea=idea,
        gap=gap,
        novelty=report,
        scores=DimensionScores(novelty=1, feasibility=1, impact=1),
        total_score=1,
    )
