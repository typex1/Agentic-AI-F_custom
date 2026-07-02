# Strands Agents SDK vs. Pydantic AI

A comparison of the two Python agent frameworks, based on the
[Strands Agents docs](https://strandsagents.com/) and the
[Pydantic AI docs](https://ai.pydantic.dev/).

## TL;DR

They are the **same category of tool**: Python "model-driven" agent frameworks.
Both give you an `Agent` configured with a model, a prompt, and tools, and both
run an agentic loop (reason → call tools → respond). If you know one, the other
feels familiar. They differ mainly in *origin* and *emphasis*:

- **Strands Agents** — from **AWS**; deepest integration with Amazon Bedrock
  and AWS deployment/tooling (AgentCore, Knowledge Bases, the strands-shell
  sandbox).
- **Pydantic AI** — from the **Pydantic team**; brings a "FastAPI feeling" to
  GenAI with strict **type-safety** and **dependency injection**, plus tight
  **Pydantic Logfire** observability.

## Side-by-side: the minimal agent

```python
# Strands
from strands import Agent
agent = Agent(
    model="amazon.nova-lite-v1:0",
    system_prompt="You are a helpful assistant. Be concise.",
)
response = agent("What are the three laws of robotics?")
print(response)
```

```python
# Pydantic AI (on Amazon Bedrock)
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

model = BedrockConverseModel("amazon.nova-lite-v1:0",
                             provider=BedrockProvider(region_name="us-east-1"))
agent = Agent(model, instructions="You are a helpful assistant. Be concise.")
result = agent.run_sync("What are the three laws of robotics?")
print(result.output)
```

See runnable versions in `strands-agents/01_basic_agent.py` and
`pydantic-ai/01_basic_agent.py` — both use Nova Lite via Bedrock and print token
usage.

## What's the same

Both frameworks provide:

- An `Agent` object with a model, prompt, and tools, running a full agent loop
- **Tool decorators** on plain Python functions (`@tool` / `@agent.tool`)
- **Structured output** via Pydantic models
  (`structured_output_model=` ≈ `output_type=`)
- **MCP** client support
- **Streaming** responses
- **Hooks / lifecycle** callbacks
- **Multi-agent** patterns and **graphs**
- A companion **evals** package (Strands Evals ≈ Pydantic Evals)
- **Human-in-the-loop** tool approval
- **OpenTelemetry**-based observability
- **Model-agnostic** provider support (OpenAI, Anthropic, Bedrock, Gemini,
  Ollama, etc.) and `llms.txt` docs + an MCP doc server for AI-assisted dev

## Key differences

| Dimension | Strands Agents | Pydantic AI |
|-----------|----------------|-------------|
| **Origin** | AWS | Pydantic team (Pydantic Validation, FastAPI ecosystem) |
| **Default model** | Amazon Bedrock (Nova / Claude) | Model-agnostic string ID (e.g. `"anthropic:claude-sonnet-4-6"`) |
| **Prompt naming** | `system_prompt=` | `instructions=` (also `system_prompt=`) |
| **Invocation** | `agent("prompt")` (callable) | `agent.run_sync(...)` / `await agent.run(...)` |
| **Result** | response object with `.metrics.get_summary()` | `AgentRunResult` with `.output` and `.usage` |
| **Signature strength** | Deep AWS integration (Bedrock, AgentCore deploy, Knowledge Bases, strands-shell sandbox) | **Type-safety & dependency injection**: `Agent[DepsType, OutputType]`, typed `RunContext`, write-time error catching |
| **Observability** | Any OTel backend | OTel, tightly integrated with **Pydantic Logfire** |
| **Durable execution** | — | First-class (Temporal, DBOS, Prefect, Restate, Airflow) |
| **Feel** | "AWS-native agent SDK" | "FastAPI for GenAI" |

## Pydantic AI's distinctive idea: typed dependency injection

Its standout feature is **type-safe dependency injection**. You declare
`deps_type` and `output_type`, and your tools/instructions receive a typed
`RunContext[Deps]`:

```python
support_agent = Agent(
    "openai:gpt-5.2",
    deps_type=SupportDependencies,   # injected, typed
    output_type=SupportOutput,       # validated Pydantic model out
)

@support_agent.tool
async def customer_balance(ctx: RunContext[SupportDependencies], include_pending: bool) -> float:
    return await ctx.deps.db.customer_balance(id=ctx.deps.customer_id, include_pending=include_pending)
```

The agent is generically typed `Agent[SupportDependencies, SupportOutput]`, so a
static type checker catches mistakes at write-time and the output is guaranteed
to be a validated `SupportOutput`. Strands uses Pydantic for structured output
too, but doesn't build the whole agent around a typed DI container.

## Which to use here

For **this environment**, Strands is the natural fit — it's AWS/Bedrock-native,
matching our Nova Lite + `bedrock-runtime:Converse` permissions. Importantly,
**Pydantic AI also supports Amazon Bedrock** (`pydantic_ai.models.bedrock`), so
it runs here too against Nova Lite (verified in `pydantic-ai/01_basic_agent.py`).

Rules of thumb:
- Want the deepest AWS deployment/tooling story? → **Strands Agents**
- Want strict typing, dependency injection, and FastAPI-style ergonomics? →
  **Pydantic AI**

Both are strong, production-oriented choices — the decision is more about
ecosystem fit and team preference than raw capability.
