"""Immutable contracts shared between stages; no infrastructure dependencies."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmpty = Annotated[str, Field(min_length=1)]
UnitScore = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]


class Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class LimitationSource(StrEnum):
    AUTHOR = "author_stated"
    REVIEWER = "reviewer"
    INFERRED = "inferred"


class Paper(Model):
    id: NonEmpty
    title: NonEmpty
    abstract: str = ""
    year: Annotated[int, Field(ge=1000, le=9999)] | None = None
    doi: str | None = None
    url: str | None = None


class Section(Model):
    id: NonEmpty
    heading: NonEmpty
    text: NonEmpty
    source: Literal["paper", "review"] = "paper"


class Document(Model):
    paper: Paper
    sections: tuple[Section, ...]

    @model_validator(mode="after")
    def unique_sections(self) -> "Document":
        ids = [section.id for section in self.sections]
        if len(ids) != len(set(ids)):
            raise ValueError("section IDs must be unique within a document")
        return self


class Evidence(Model):
    paper_id: NonEmpty
    section_id: NonEmpty
    quote: Annotated[str, Field(min_length=8)]


class Claim(Model):
    text: NonEmpty
    evidence: Evidence


class Limitation(Claim):
    source: LimitationSource


class Problem(Model):
    statement: NonEmpty
    canonical: NonEmpty


class Method(Model):
    name: NonEmpty
    category: NonEmpty
    mechanism: NonEmpty


class Extraction(Model):
    paper_id: NonEmpty
    problem: Problem
    methods: tuple[Method, ...] = Field(min_length=1)
    datasets: tuple[str, ...] = ()
    metrics: tuple[str, ...] = ()
    limitations: tuple[Limitation, ...] = ()
    future_work: tuple[Claim, ...] = ()
    task_domain: NonEmpty
    contribution_type: Literal["new method", "new dataset", "analysis", "survey"]


class CanonicalEntity(Model):
    id: NonEmpty
    kind: Literal["problem", "method"]
    name: NonEmpty
    aliases: tuple[str, ...] = ()


class ContextPaper(Model):
    """Metadata/abstract plus extracted claims for a retrieved paper."""

    paper: Paper
    extraction: Extraction

    @model_validator(mode="after")
    def consistent_paper(self) -> "ContextPaper":
        if self.paper.id != self.extraction.paper_id:
            raise ValueError("context paper and extraction IDs differ")
        return self


class GenerationContext(Model):
    papers: tuple[ContextPaper, ...] = ()
    neighboring_entities: tuple[CanonicalEntity, ...] = ()


class Gap(Model):
    id: NonEmpty
    kind: Literal["matrix", "pain_point"]
    description: NonEmpty
    evidence_paper_ids: tuple[NonEmpty, ...] = Field(min_length=1)
    score: UnitScore
    problem_entity_id: str | None = None
    method_entity_id: str | None = None


class ExperimentPlan(Model):
    datasets: tuple[NonEmpty, ...] = Field(min_length=1)
    baselines: tuple[NonEmpty, ...] = Field(min_length=1)
    metrics: tuple[NonEmpty, ...] = Field(min_length=1)


class Idea(Model):
    id: NonEmpty
    gap_id: NonEmpty
    title: NonEmpty
    problem: NonEmpty
    method_steps: tuple[NonEmpty, ...] = Field(min_length=1)
    experiment: ExperimentPlan
    expected_contributions: tuple[NonEmpty, ...] = Field(min_length=1)
    risks: tuple[NonEmpty, ...] = Field(min_length=1)

    def similarity_text(self) -> str:
        """Text used for within-batch deduplication."""
        return f"{self.title}\n{self.problem}"

    def full_text(self) -> str:
        """Include method and evaluation details in prior-art screening."""
        return self.model_dump_json()


class Review(Model):
    idea_id: NonEmpty
    dimension: Literal["novelty", "feasibility", "clarity"]
    comments: tuple[NonEmpty, ...]
    requires_revision: bool


class Overlap(StrEnum):
    IDENTICAL = "identical"
    HIGH = "high_overlap"
    DISTINCT = "related_but_distinct"
    UNRELATED = "unrelated"


class PriorArt(Model):
    paper: Paper
    overlap: Overlap
    difference: NonEmpty
    similarity: Annotated[float, Field(ge=-1, le=1, allow_inf_nan=False)]


class NoveltyReport(Model):
    idea_id: NonEmpty
    search_complete: bool
    queries: tuple[NonEmpty, ...]
    neighbors: tuple[PriorArt, ...] = ()

    @property
    def eligible(self) -> bool:
        return (
            self.search_complete
            and bool(self.queries)
            and not any(n.overlap in {Overlap.IDENTICAL, Overlap.HIGH} for n in self.neighbors)
        )


class DimensionScores(Model):
    novelty: UnitScore
    feasibility: UnitScore
    impact: UnitScore


class IdeaCard(Model):
    idea: Idea
    gap: Gap
    novelty: NoveltyReport
    scores: DimensionScores
    total_score: UnitScore
    human_decision: Literal["pending", "adopt", "skip"] = "pending"

    @model_validator(mode="after")
    def check_lineage(self) -> "IdeaCard":
        if self.idea.gap_id != self.gap.id or self.novelty.idea_id != self.idea.id:
            raise ValueError("card provenance IDs do not agree")
        if not self.novelty.eligible:
            raise ValueError("card requires a completed, non-overlapping novelty report")
        return self
