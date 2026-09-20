"""Step 3 + 4 output contracts: the Pydantic models behind Strands structured output.

This is the heart of the teaching example. In the Langdock builder the two agent
nodes had a flat "Structured Output" table (name, type, description), and the
shape of each array element had to be *described in prose* inside the field
description, then parsed defensively in the Code node.

In Strands the schema is real code. A Pydantic model is:

  1. converted to a JSON Schema and registered as a *tool* the model must call,
  2. validated by Pydantic when the model calls that tool,
  3. handed back to you as a typed Python object in ``result.structured_output``.

Everything you write here (field descriptions, ``Literal`` enums, numeric
bounds, nested models, custom validators) ends up either in the tool schema the
model sees, or in the validation step that rejects a bad answer and makes the
model try again. See ``explain_structured_output.py`` for a look under the hood.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# --- Shared vocabularies -----------------------------------------------------
# ``Literal`` becomes an ``enum`` in the JSON schema, so the model can only pick
# one of these values. In the Langdock version this was a sentence in the
# description ("category (string: hard_skill, experience, ...)") that the model
# could ignore.
Category = Literal[
    "hard_skill",
    "experience",
    "education",
    "language",
    "soft_skill",
    "certification",
    "other",
]
Priority = Literal["must", "nice"]


# --- Agent 1: JD Requirement Extractor ---------------------------------------
class Requirement(BaseModel):
    """One concrete requirement from the job description."""

    id: str = Field(
        description="Sequential id: R1, R2, R3, ...",
        pattern=r"^R\d+$",
    )
    text: str = Field(description="Normalised requirement, one distinct skill/experience/degree/language/certification.")
    category: Category = Field(description="Type of requirement.")
    priority: Priority = Field(
        description='"must" if required/mandatory/minimum, "nice" if optional/preferred/bonus.'
    )
    weight: int = Field(
        description="Importance for the role: 5 = central, 1 = peripheral. Must-haves are >= 3, nice-to-haves are <= 3.",
        ge=1,
        le=5,
    )
    source: str = Field(description="Verbatim quote from the job description that this requirement is based on.")

    @model_validator(mode="after")
    def weight_matches_priority(self) -> "Requirement":
        """Cross-field rule. If it fails, Strands feeds the error message back to the
        model as a tool error and the model produces a corrected answer."""
        if self.priority == "must" and self.weight < 3:
            raise ValueError(f"{self.id}: must-have requirements need weight >= 3 (got {self.weight})")
        if self.priority == "nice" and self.weight > 3:
            raise ValueError(f"{self.id}: nice-to-have requirements need weight <= 3 (got {self.weight})")
        return self


class JobRequirements(BaseModel):
    """Structured output of the JD Requirement Extractor agent.

    The docstring becomes the tool description the model sees, so keep it useful.
    """

    role_title: str = Field(description="Job title as stated in the job description.")
    requirements: list[Requirement] = Field(
        description="One element per distinct requirement, roughly 12-25 for a typical job description.",
        min_length=1,
    )

    @model_validator(mode="after")
    def ids_are_unique(self) -> "JobRequirements":
        ids = [r.id for r in self.requirements]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            raise ValueError(f"requirement ids must be unique, duplicates: {duplicates}")
        return self


# --- Agent 2: CV Assessor ----------------------------------------------------
class Assessment(BaseModel):
    """How well the CV covers one requirement."""

    requirement_id: str = Field(description="The id (R1, R2, ...) of the requirement being assessed.")
    fulfilment: int = Field(
        description="3 = fully met and explicitly evidenced, 2 = largely met, 1 = partial/weak evidence, 0 = not met / no evidence.",
        ge=0,
        le=3,
    )
    evidence: str = Field(description="Quoted CV passage supporting the rating. Empty string if there is no evidence.")
    comment: str = Field(description="One sentence explaining the rating.")

    @model_validator(mode="after")
    def evidence_backs_rating(self) -> "Assessment":
        """A positive rating without a quote is exactly the kind of hallucination
        we want to catch, so make it a hard validation error."""
        if self.fulfilment > 0 and not self.evidence.strip():
            raise ValueError(
                f"{self.requirement_id}: fulfilment {self.fulfilment} needs a quoted CV passage in 'evidence' "
                "(or set fulfilment to 0)"
            )
        return self


class CVAssessment(BaseModel):
    """Structured output of the CV Assessor agent."""

    candidate_name: str = Field(description="Full candidate name as written in the CV.")
    assessments: list[Assessment] = Field(
        description="Exactly one element per requirement, in the same order as the requirement list.",
        min_length=1,
    )
    additional_strengths: list[str] = Field(
        description="Up to 5 relevant qualifications the candidate offers that the job description did not ask for.",
        max_length=5,
    )
