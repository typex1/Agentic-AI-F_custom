# 11 — Multi-Agent Graph

**Python file:** [`../11_graph.py`](../11_graph.py)

## Learning objective
Orchestrate multiple agents in an explicit, **deterministic** topology where you
define exactly who feeds whom, and outputs flow along the edges.

## Why it matters
The third multi-agent topology (with agents-as-tools in 05 and swarm in 10).
When you know the workflow in advance, a graph gives you predictable,
reproducible orchestration instead of emergent behavior — ideal for pipelines.

## What this example demonstrates
- Building a "star + fan-in" topology with `GraphBuilder`: a coordinator fans
  out to three parallel analysts, who fan in to a synthesizer.
- Defining nodes (agents) and edges (communication paths) explicitly.
- Setting an entry point and reading the resulting `execution_order`.

## Key concepts
`GraphBuilder`, nodes/edges, deterministic DAG orchestration, fan-out/fan-in,
`set_entry_point`, `result.execution_order`.
