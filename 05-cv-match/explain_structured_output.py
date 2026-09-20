"""What happens when you pass ``structured_output_model=`` to a Strands agent.

Three short demonstrations, in the order things happen at runtime:

  Part 1  Pydantic model  -> tool spec (JSON Schema) the LLM sees        [offline]
  Part 2  Bad tool input  -> Pydantic ValidationError the LLM gets back  [offline]
  Part 3  A live agent call that is forced into a validation retry       [--live, calls Bedrock]

Run:
    python explain_structured_output.py          # parts 1 + 2, no credentials needed
    python explain_structured_output.py --live   # also part 3
"""

import json
import sys
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator
from strands.tools.structured_output.structured_output_utils import convert_pydantic_to_tool_spec

from cv_match.schemas import JobRequirements, Requirement


def part1_tool_spec() -> None:
    print("=" * 78)
    print("PART 1  The Pydantic model becomes a *tool* the model must call")
    print("=" * 78)
    print(
        "Strands does not ask the model for 'JSON please'. It converts the Pydantic class\n"
        "into a tool specification and forces the model to call that tool. Field descriptions,\n"
        "Literal enums, min/max, patterns and nested models all land in the schema:\n"
    )
    spec = convert_pydantic_to_tool_spec(JobRequirements)
    print(json.dumps(spec, indent=2, ensure_ascii=False))
    print(
        "\nCompare with the Langdock builder, where `requirements` was an untyped Array whose\n"
        "element keys were described in a sentence. Here `items` is a full object schema."
    )


def part2_validation_errors() -> None:
    print()
    print("=" * 78)
    print("PART 2  When the model's tool call does not fit, Pydantic explains why")
    print("=" * 78)
    print(
        "Strands validates the tool input with the Pydantic model. On failure the error text\n"
        "is returned to the model as a *tool error*, and the model gets another attempt.\n"
        "This is the message the model would receive for a sloppy requirement:\n"
    )
    bad_input = {
        "id": "req-1",  # violates pattern ^R\d+$
        "text": "Python",
        "category": "programming",  # not in the Literal
        "priority": "must",
        "weight": 9,  # > 5
        # "source" missing
    }
    try:
        Requirement(**bad_input)
    except ValidationError as e:
        print(str(e))

    print("\nAnd the cross-field rule from the model_validator (must-have with weight 1):\n")
    try:
        Requirement(id="R1", text="Python", category="hard_skill", priority="must", weight=1, source="Python required")
    except ValidationError as e:
        print(str(e))


def part3_live_retry() -> None:
    print()
    print("=" * 78)
    print("PART 3  Live: watch the validation retry loop (calls Amazon Bedrock)")
    print("=" * 78)

    from strands import Agent

    from cv_match.agents import make_model

    class Weighted(BaseModel):
        """A requirement with a priority and a weight."""

        text: str
        priority: Literal["must", "nice"]
        weight: int = Field(ge=1, le=5, description="1 = peripheral, 5 = central")

        @model_validator(mode="after")
        def must_has_weight(self) -> "Weighted":
            if self.priority == "must" and self.weight < 3:
                raise ValueError("must-have requirements need weight >= 3; please raise the weight")
            return self

    agent = Agent(
        model=make_model(),
        system_prompt=(
            "You convert records into the requested structure exactly as given. "
            "If validation fails, fix the offending value and try again. Never ask questions."
        ),
        callback_handler=None,
    )
    # Deliberately hand over a record the validator rejects. The first tool call
    # (weight 1, priority must) fails validation; the model has to correct itself.
    result = agent(
        "Record: text=Python, priority=must, weight=1",
        structured_output_model=Weighted,
    )

    print("Final validated object:", result.structured_output, "\n")
    print("Message history (toolUse = model attempt, toolResult = Strands' answer):")
    for msg in agent.messages:
        for block in msg["content"]:
            if "toolUse" in block:
                print(f"  {msg['role']:9s} toolUse   {block['toolUse']['name']} {json.dumps(block['toolUse']['input'])}")
            elif "toolResult" in block:
                tr = block["toolResult"]
                text = " ".join(c.get("text", "") for c in tr["content"])[:160].replace("\n", " ")
                print(f"  {msg['role']:9s} toolResult status={tr['status']}: {text}")
            elif "text" in block and block["text"].strip():
                print(f"  {msg['role']:9s} text      {block['text'][:120].replace(chr(10), ' ')}")


if __name__ == "__main__":
    part1_tool_spec()
    part2_validation_errors()
    if "--live" in sys.argv:
        part3_live_retry()
    else:
        print("\n(Run with --live to see part 3, a real agent call with a forced validation retry.)")
