"""Steps 3 + 4: the two Strands agents with structured output.

Equivalent of the Langdock agent nodes `agent` (JD Requirement Extractor) and
`agent2` (Assess CV per requirement). Each function

  1. builds an ``Agent`` with a system prompt and a low-temperature Bedrock model,
  2. calls it once with the document(s) as the user message,
  3. passes ``structured_output_model=<PydanticModel>``,
  4. returns ``result.structured_output`` - already a validated Python object.

No JSON parsing, no ``json.loads``, no "hope the model used the right keys".
"""

import json
import os

from strands import Agent
from strands.models.bedrock import BedrockModel

from .prompts import (
    ASSESSOR_SYSTEM_PROMPT,
    ASSESSOR_USER_TEMPLATE,
    EXTRACTOR_SYSTEM_PROMPT,
    EXTRACTOR_USER_TEMPLATE,
)
from .schemas import CVAssessment, JobRequirements

# Langdock used "GPT-5.6 Luna" with creativity 0.1-0.2. Here: Bedrock, any model
# that supports tool use. Default is Nova Lite (the only model permitted in the
# class environment); override with CV_MATCH_MODEL_ID (e.g. a us.anthropic.… or
# global.anthropic.… inference profile id) for more precise ratings.
DEFAULT_MODEL_ID = os.environ.get("CV_MATCH_MODEL_ID", "amazon.nova-lite-v1:0")


def make_model(model_id: str | None = None) -> BedrockModel:
    return BedrockModel(
        model_id=model_id or DEFAULT_MODEL_ID,
        temperature=0.1,
        max_tokens=8000,
        # Optional: strict_tools=True asks Bedrock to enforce the tool schema
        # server-side on top of Pydantic's client-side validation.
    )


def extract_requirements(jd_text: str, notes: str = "", model_id: str | None = None) -> JobRequirements:
    """Langdock node `agent`: job description text -> JobRequirements."""
    agent = Agent(
        name="JD Requirement Extractor",
        model=make_model(model_id),
        system_prompt=EXTRACTOR_SYSTEM_PROMPT,
        callback_handler=None,  # quiet: no token streaming to stdout
    )
    result = agent(
        EXTRACTOR_USER_TEMPLATE.format(notes=notes or "none", jd_text=jd_text),
        structured_output_model=JobRequirements,
    )
    # result.structured_output is a JobRequirements instance (or the call raised
    # StructuredOutputException after the built-in validation retries gave up).
    return result.structured_output


def assess_cv(reqs: JobRequirements, cv_text: str, model_id: str | None = None) -> CVAssessment:
    """Langdock node `agent2`: (requirements, CV text) -> CVAssessment.

    The requirement list is the *output object of step 3*, serialised with
    ``model_dump_json`` - in Langdock this was the template variable
    ``{{agent?.output.structured.requirements}}``.
    """
    agent = Agent(
        name="CV Assessor",
        model=make_model(model_id),
        system_prompt=ASSESSOR_SYSTEM_PROMPT,
        callback_handler=None,
    )
    requirements_json = json.dumps(
        [r.model_dump(include={"id", "text", "category", "priority"}) for r in reqs.requirements],
        indent=1,
        ensure_ascii=False,
    )
    result = agent(
        ASSESSOR_USER_TEMPLATE.format(requirements_json=requirements_json, cv_text=cv_text),
        structured_output_model=CVAssessment,
    )
    return result.structured_output
