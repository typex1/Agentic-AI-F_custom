# CrewAI Examples

The [`01-fundamentals/`](../01-fundamentals/) examples, rebuilt with the [CrewAI](https://docs.crewai.com/) framework — same concepts, same Amazon Nova Lite model, different framework. Use these side-by-side with the Strands versions to compare the two SDKs.

> `00_bedrock_direct.py` has no counterpart here on purpose: it calls the raw Bedrock Converse API without any agent framework, so it is framework-independent — see the original in `01-fundamentals/`.

## Learning Path

| # | File | Concept | Strands counterpart |
|---|------|---------|---------------------|
| 1 | `01_basic_agent.py` | Simplest agent — role/goal/backstory + Task + Crew | `01-fundamentals/01_basic_agent.py` |
| 2 | `02_custom_tools.py` | Custom tools with the `@tool` decorator | `01-fundamentals/02_custom_tools.py` |
| 3 | `03_logging.py` | Observability via the event bus | `01-fundamentals/03_logging.py` |
| 4 | `04_structured_output.py` | Typed output with `output_pydantic` | `01-fundamentals/04_structured_output.py` |

All examples use **`bedrock/amazon.nova-lite-v1:0`** — the same model as the Strands versions (CrewAI routes model IDs through LiteLLM, hence the `bedrock/` prefix).

## Prerequisites

```bash
pip install crewai ddgs pydantic
```

AWS credentials with Bedrock access to Nova Lite, as for the Strands examples.

## Running

```bash
# From the repo root:
python crewai/01_basic_agent.py
```

Each file is self-contained and runnable independently.

## Strands ↔ CrewAI: the mental-model shift

| Concept | Strands | CrewAI |
|---|---|---|
| Agent definition | `Agent(model=..., system_prompt=...)` | `Agent(role=..., goal=..., backstory=..., llm=...)` — the persona fields build the system prompt |
| Running | Call the agent like a function: `agent("...")` | Declare a `Task`, bundle into a `Crew`, run `crew.kickoff()` |
| Model ID | `"amazon.nova-lite-v1:0"` (Bedrock-native) | `"bedrock/amazon.nova-lite-v1:0"` (LiteLLM routing) |
| Custom tools | `@tool` decorator | `@tool("name")` decorator — same idea, name passed explicitly |
| Built-in tools | `strands-agents-tools` (calculator, shell, current_time, …) | No equivalent basics in `crewai-tools` (it focuses on RAG/search/scraping) → written as custom tools here |
| Direct tool call | `agent.tool.unit_converter(...)` | `unit_converter.run(...)` |
| Observability | Per-agent hooks API (`hooks=[...]`, `BeforeToolCallEvent`, …) | Global event bus (`BaseEventListener`, `ToolUsageStartedEvent`, `LLMCallStartedEvent`, …) |
| Structured output | `structured_output_model=` on the agent call → `result.structured_output` | `output_pydantic=` on the Task → `result.pydantic` |
| Token metrics | `response.metrics.get_summary()` | `result.token_usage` |

### Feature-parity notes (found while porting)

- **Structured output IS available** in CrewAI — it just lives on the `Task` (`output_pydantic`), not on the call. Validated Pydantic instances come back on `result.pydantic`.
- **No calculator/shell built-ins**: implemented as custom tools in `02_custom_tools.py` (a few lines each — packaging difference, not a capability gap).
- **No tool-consent mechanism**: Strands' `shell` tool prompts for confirmation unless `BYPASS_TOOL_CONSENT=true`; CrewAI executes tools without asking. The custom shell tool here is demo-only.
- **Telemetry**: CrewAI sends OpenTelemetry traces by default; every example disables this via env vars *before* importing crewai (`CREWAI_TRACING_ENABLED=false`, `CREWAI_DISABLE_TELEMETRY=true`, `OTEL_SDK_DISABLED=true`). Without this, scripts hang ~60 s at exit on machines that can't reach the collector.

## Log Output

The `logs/` directory contains sample output from `03_logging.py` showing the tool catalog, per-turn prompts, and tool call/result lines captured through the event bus.
