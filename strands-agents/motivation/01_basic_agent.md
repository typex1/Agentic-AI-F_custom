# Basic Agent

**Python file:** [`../01_basic_agent.py`](../01_basic_agent.py)

## Learning objective
Build the simplest possible agent and understand the core agent loop before
adding any complexity.

## Why it matters
Everything else in this collection builds on this foundation. If you understand
how a bare agent is created, prompted, and how its result/metrics are read, the
rest is incremental.

## What this example demonstrates
- Creating an `Agent` with just a model and a `system_prompt`.
- Calling the agent like a function and printing the response.
- Reading usage metrics (tokens, latency, loop cycles) from the result via
  `response.metrics.get_summary()`.

## Key concepts
`Agent`, `system_prompt`, the agent loop
(Input → Reasoning → Tool Selection → Tool Execution → Response), result metrics.
