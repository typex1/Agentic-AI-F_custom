# Multi-Agent: Agents as Tools

**Python file:** [`../08_multi_agent.py`](../08_multi_agent.py)

## Learning objective
Compose multiple specialized agents by wrapping them as tools that a
coordinator agent can call — the simplest multi-agent pattern.

## Why it matters
Complex tasks are easier to solve by delegating to focused specialists. This is
the entry point to multi-agent systems and contrasts with the swarm (10) and
graph (11) topologies covered later.

## What this example demonstrates
- Building specialist agents (`code_reviewer`, `explainer`) each with a narrow
  role.
- Wrapping each specialist as a `@tool` so an **orchestrator** agent can invoke
  it on demand.
- The orchestrator deciding which specialist(s) to delegate to based on the
  request.

## Key concepts
Agents-as-tools pattern, orchestrator/specialist decomposition, delegation via
tool calls.
