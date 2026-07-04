# Student Tasks — Day 2 (Build & Secure)

Hands-on tasks for experienced developers who are new to agentic AI frameworks.
Every task runs on **Amazon Nova Lite** (`amazon.nova-lite-v1:0`) via Amazon
Bedrock — the only model available in this environment (see
[`../../.kiro/steering/Permissions.md`](../../.kiro/steering/Permissions.md)).

Each task is a self-contained assignment. A **verified reference solution** lives
under [`../solutions/`](../solutions/) — attempt the task first, then compare.

## The tasks

| # | Task | Day-2 module(s) | Builds on (demos) | Reference solution |
|---|------|-----------------|-------------------|--------------------|
| 1 | [Minimal Kiro-CLI replica](1-kiro-replica.md) | 1–2 · Setup & first agent | `01`, `02`, `04` | [`solutions/1-kiro-replica/`](../solutions/1-kiro-replica/) |
| 2 | [Typed, read-only API tools](2-typed-api-tools.md) | 2 · Agent + API-Tools | `02`, `03` | [`solutions/2-typed-api-tools/`](../solutions/2-typed-api-tools/) |
| 3 | [RAG over a KB via your own MCP server](3-rag-and-mcp.md) | 3 · RAG & MCP | `07`, `08` | [`solutions/3-rag-and-mcp/`](../solutions/3-rag-and-mcp/) |
| 4 | [Harness, guardrails & prompt injection](4-guardrails-and-injection.md) | 4–5 · Guardrails + Lethal Trifecta | `09` | [`solutions/4-guardrails-and-injection/`](../solutions/4-guardrails-and-injection/) |
| 5 | [Use `skill-creator` to author a skill](5-skill-creator.md) | Capstone · Agent Skills | `13` | *(worked try-out in [`../experiments/skill-creator/`](../experiments/skill-creator/))* |
| 6 | [RAG over a Google OKF knowledge base](6-rag-okf.md) | 3 · RAG & MCP | `08` (`08_RAG_OKF.py`) | [`../08_RAG_OKF.py`](../08_RAG_OKF.py) |

## Suggested progression

Tasks 1 → 4 follow the day-2 arc and build on each other: a basic tool-using
agent, then typed API reads, then retrieval + MCP, then acting safely under
guardrails. Task 2's station tools are reused (with a guarded *write* added) in
Task 4. Task 5 is a standalone capstone on Agent Skills.

Module 6 (Productive & Outlook) is conceptual and is better handled as discussion
than a hands-on task.

## Prerequisites

```bash
pip install -r ../../requirements.txt
```

Plus AWS credentials with `bedrock-runtime` access to Nova Lite in `us-east-1`.
Some tasks reference the demos in [`../`](../) — read the matching demo before
starting a task.
