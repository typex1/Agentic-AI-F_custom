# 01 — Basic Agent (Pydantic AI)

**Python file:** [`../01_basic_agent.py`](../01_basic_agent.py)

## Learning objective
Build the simplest possible **Pydantic AI** agent and see how it compares, line
for line, with the Strands equivalent in
[`strands-agents/01_basic_agent.py`](../../strands-agents/01_basic_agent.py).

## Why it matters
Pydantic AI is a peer framework to Strands (see
[`StrandsAgents_vs_PydanticAI.md`](../../StrandsAgents_vs_PydanticAI.md)). Seeing
the same minimal agent in both frameworks makes the similarities (an `Agent`
with a model, instructions, and a run) and differences (typed results, model
configuration) concrete.

## What this example demonstrates
- Creating a Pydantic AI `Agent` with `instructions` (its term for the system
  prompt).
- Configuring it to run on **Amazon Bedrock + Nova Lite** via
  `BedrockConverseModel` + `BedrockProvider` — staying within this environment's
  `bedrock-runtime:Converse` permission.
- Running synchronously with `run_sync(...)` and reading `.output`.
- Reading token usage from `result.usage`.

## Key concepts
Pydantic AI `Agent`, `instructions`, `BedrockConverseModel`/`BedrockProvider`,
`run_sync`, `result.output`, `result.usage`; model-agnostic frameworks running
on the same Bedrock model.
