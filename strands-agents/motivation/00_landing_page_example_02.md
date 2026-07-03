# 00 — Landing Page Example

**Python file:** [`../00_landing_page_example_02.py`](../00_landing_page_example_02.py)

## Learning objective
See the "few lines of code" pitch in action: a complete, useful agent — model,
a custom tool, and a policy-enforcing hook — in one short file.

## Why it matters
It sets the tone for the whole collection: Strands agents are just Python. You
don't need scaffolding or config to get an agent that takes real actions.

## What this example demonstrates
- A custom `@tool` (`save_report`) the agent calls autonomously.
- A `BeforeToolCallEvent` **hook** used as a guardrail: it cancels the save
  unless the report includes source citations, feeding the reason back to the
  model so it self-corrects and retries.
- End-to-end flow from a single prompt to a validated side effect (a file
  written to disk).

## Key concepts
`Agent`, `@tool`, lifecycle hooks (`BeforeToolCallEvent`, `event.cancel_tool`).
