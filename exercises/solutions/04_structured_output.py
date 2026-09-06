"""
04_structured_output.py — Structured output for a support ticket (Strands + Nova Lite)

Solution for exercises/tasks/04_structured_output.md:
  - A Pydantic model (`SupportTicket`) defines the shape of the answer.
  - `structured_output_model=` makes the agent return that model, validated.
  - Fields are accessed programmatically — no free-text parsing.

Run:
  python 04_structured_output.py
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from typing import Literal

from pydantic import BaseModel, Field
from strands import Agent


class SupportTicket(BaseModel):
    """A support ticket extracted from a free-text customer message."""

    customer_name: str = Field(description="The customer's name as given in the message")
    topic: str = Field(description="Short topic of the issue, e.g. 'billing', 'shipping'")
    urgency: Literal["low", "medium", "high"] = Field(
        description="How urgent the issue is, judged from tone and deadlines"
    )
    summary: str = Field(description="One-sentence summary of the issue")


agent = Agent(
    model="amazon.nova-lite-v1:0",  # the only model permitted in this environment
    system_prompt="You extract structured support tickets from customer messages.",
    callback_handler=None,
)


def extract(message: str) -> SupportTicket:
    result = agent(
        f"Extract a support ticket from this customer message:\n\n{message}",
        structured_output_model=SupportTicket,
    )
    return result.structured_output


def show(ticket: SupportTicket) -> None:
    print(f"  customer_name: {ticket.customer_name}")
    print(f"  topic:         {ticket.topic}")
    print(f"  urgency:       {ticket.urgency}   (guaranteed one of low/medium/high)")
    print(f"  summary:       {ticket.summary}")
    print()


print("=== Clear message ===")
show(extract(
    "Hi, this is Maria. My invoice from last month shows the wrong amount "
    "and I need this fixed before Friday!"
))

print("=== Ambiguous message (no name, no deadline) ===")
show(extract(
    "The app sometimes feels a bit slow in the evenings, no big deal though."
))
