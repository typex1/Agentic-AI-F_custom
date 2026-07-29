# 10 — Multi-Agent Swarm

**Python file:** [`../13_swarm.py`](../13_swarm.py)

## Learning objective
Coordinate a team of specialized agents that **self-organize** — handing off to
each other autonomously with shared context, without a central controller.

## Why it matters
This is one of the three multi-agent topologies (alongside agents-as-tools in 05
and graph in 11). Swarms suit open-ended problems where the best sequence of
specialists isn't known in advance and should emerge at runtime.

## What this example demonstrates
- Building named specialist agents (`researcher`, `architect`, `coder`,
  `reviewer`) with strictly scoped roles that force handoffs.
- Assembling them into a `Swarm` with handoff/iteration limits and loop
  detection.
- Observing the emergent handoff path (e.g. the reviewer sending work back to
  the coder).

## Key concepts
`Swarm`, autonomous handoffs, shared working memory, `result.node_history`,
handoff/iteration safety limits.
