# 02 — System Prompt & Dependencies (Pydantic AI)

**Python file:** [`../02_system_prompt_dependencies.py`](../02_system_prompt_dependencies.py)

## Learning objective
Move beyond a static instruction string: build a **dynamic system prompt** that
is generated at run time from **injected dependencies**, using Pydantic AI's
`deps_type` + `RunContext` dependency-injection mechanism.

## Why it matters
Real agents rarely have a fixed system prompt. They need context that only exists
at run time — a user profile, the current date, data fetched from an API, a
tenant's configuration. Pydantic AI makes this **type-safe**: you declare a
dependencies type, and every dynamic prompt and tool receives it through a typed
`RunContext`. This is the same idea as dependency injection in a web framework,
applied to agents — no globals, no hidden state, and the type checker has your
back.

## What this example demonstrates
- Declaring a typed dependencies dataclass (`MyDeps`) holding an API key and a
  shared `httpx.AsyncClient`.
- Wiring it into the agent with `Agent(model, deps_type=MyDeps)`.
- A **dynamic** system prompt via the `@agent.system_prompt` decorator, which
  receives a `RunContext[MyDeps]` and can `await` I/O (here, an async HTTP call)
  to build the prompt on the fly.
- Passing dependencies per run with `await agent.run(..., deps=deps)` inside an
  `asyncio` event loop.
- Running on **Amazon Bedrock + Nova Lite** via `BedrockConverseModel` +
  `BedrockProvider`, staying within this environment's `bedrock-runtime:Converse`
  permission.

## Key concepts
Pydantic AI `deps_type`, `RunContext[Deps]`, `@agent.system_prompt` (dynamic vs.
static `instructions`), typed dependency injection, async agent runs
(`await agent.run(...)` / `asyncio.run`), sharing an `httpx.AsyncClient` as a
dependency.
