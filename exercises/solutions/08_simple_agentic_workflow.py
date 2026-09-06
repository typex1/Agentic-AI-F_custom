"""
08_simple_agentic_workflow.py — Classify → route → draft (Strands + Nova Lite)

Solution for exercises/tasks/08_simple_agentic_workflow.md:
  - Stage 1 (LLM, structured output): classify a product review into a typed
    verdict (sentiment + product).
  - Routing (plain Python): dictionary dispatch on the validated sentiment.
  - Stage 2 (LLM): a sentiment-specific agent drafts the reply.
  - Bonus: three reviews processed concurrently with asyncio.gather.

Design rule: LLM where judgment is needed (classify, draft), plain Python
where determinism is needed (routing).

Run:
  python 08_simple_agentic_workflow.py
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import asyncio
from typing import Literal

from pydantic import BaseModel, Field
from strands import Agent


MODEL_ID = "amazon.nova-lite-v1:0"  # the only model permitted in this environment

SYSTEM_PROMPTS = {
    "classifier": "You classify product reviews.",
    "positive": (
        "You write a short, warm thank-you reply (2-3 sentences) to a happy "
        "customer. Mention the product by name."
    ),
    "negative": (
        "You write a short apology (2-3 sentences) to an unhappy customer, "
        "mention the product by name, and end with exactly ONE clarifying "
        "question that helps resolve the problem."
    ),
}


# --- Stage 1: classifier returns a TYPED verdict -------------------------
class ReviewVerdict(BaseModel):
    """Classification of a product review."""

    sentiment: Literal["positive", "negative"] = Field(
        description="Overall sentiment of the review"
    )
    product: str = Field(description="The product the review is about")


async def handle_review(review: str) -> str:
    # NOTE: one Agent instance cannot serve concurrent requests
    # (ConcurrencyException) — with asyncio.gather each review therefore
    # gets its own agent instances. Agents are cheap to create.

    # Stage 1 — classify (LLM + validation)
    classifier = Agent(model=MODEL_ID, system_prompt=SYSTEM_PROMPTS["classifier"],
                       callback_handler=None)
    result = await classifier.invoke_async(
        f"Classify this review:\n\n{review}",
        structured_output_model=ReviewVerdict,
    )
    verdict = result.structured_output

    # Routing — deterministic dictionary dispatch on the VALIDATED verdict;
    # plain Python decides which specialist runs, no LLM involved.
    responder = Agent(model=MODEL_ID, system_prompt=SYSTEM_PROMPTS[verdict.sentiment],
                      callback_handler=None)

    # Stage 2 — draft the reply (LLM)
    reply = await responder.invoke_async(
        f"The customer wrote about {verdict.product}:\n\n{review}"
    )
    return f"[{verdict.sentiment} | {verdict.product}]\n{reply}"


REVIEWS = [
    "The espresso machine is fantastic, best purchase this year!",
    "The blender died after two days and support never answered.",
    "Love the standing desk — assembly took 15 minutes and it is rock solid.",
]


async def main() -> None:
    # Bonus: parallelization — all reviews processed concurrently
    replies = await asyncio.gather(*(handle_review(r) for r in REVIEWS))
    for review, reply in zip(REVIEWS, replies):
        print(f"REVIEW: {review}")
        print(f"{reply}")
        print("-" * 70)


if __name__ == "__main__":
    asyncio.run(main())
