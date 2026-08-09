# Strands Agents SDK — Demo Content

The **Strands Agents SDK** (`strands-agents`) is the core Python SDK for building AI agents. It provides a model-driven approach where agents autonomously decide which tools to use, how to chain them, and when to respond — all in just a few lines of code.

## Why the Strands Agents SDK?

| Feature | What it gives you |
|---------|-------------------|
| **Agent Loop** | Autonomous reasoning → tool selection → execution → response cycle |
| **@tool Decorator** | Turn any Python function into an agent-callable tool with zero boilerplate |
| **Multi-Model** | Swap between Bedrock, OpenAI, Anthropic, Ollama, etc. with one line |
| **Structured Output** | Get typed Pydantic models back from your agents |
| **Streaming** | Real-time token-by-token output via callbacks or async iterators |
| **Multi-Agent** | Compose agents as tools for other agents (agents-as-tools pattern) |
| **Session Management** | Persist and resume conversations across invocations |
| **MCP Integration** | Consume tools from external MCP servers (local or remote) |
| **Observability** | Built-in traces, metrics, and OpenTelemetry export |

## Demos

| File | Concept |
|------|---------|
| `01_basic_agent.py` | Simplest possible agent — 3 lines of code |
| `02_custom_tools.py` | Creating custom tools with the `@tool` decorator |
| `03_logging.py` | Observing tool use through logging — tool catalog + prompt/context in the log |
| `04_structured_output.py` | Getting typed Pydantic responses from agents |
| `05_mcp_tools.py` | Consuming tools from an MCP server (AWS Knowledge MCP) |
| `06_agent-skill.py` | Integrating an Agent Skill (Anthropic frontend-design) via the AgentSkills plugin |
| `07_RAG_1.py` | Adaptive structured RAG (NL2SQL) agent with self-correction |
| `08_multi_agent.py` | Agents-as-tools pattern for delegation |
| `09_graph.py` | Multi-agent graph — deterministic star + fan-in topology |
| `10_session_management.py` | Persisting conversations to disk |
| `11_swarm.py` | Multi-agent swarm — self-organizing team with handoffs |
| `12_conversation_management.py` | Sliding-window, null, and summarizing history managers |

## Exercises

| Path | Concept |
|------|---------|
| `solutions/Customer-Support-Tickets/` | Exercise + peekable reference solution: all four workflow patterns (chaining, parallelization, orchestration, routing) in one support workflow — see its `TASK.md` |

## Prerequisites

```bash
pip install strands-agents strands-agents-tools
```

These demos use **Amazon Bedrock** with the **Amazon Nova Lite** model (`amazon.nova-lite-v1:0`) in `us-east-1`. Ensure your environment has `bedrock-runtime:Converse` permissions.

`05_mcp_tools.py` additionally connects to the public **AWS Knowledge MCP server** (`https://knowledge-mcp.global.api.aws`) over Streamable HTTP — it requires internet access but no authentication. The `mcp` client library ships with `strands-agents`.

`06_agent-skill.py` downloads Anthropic's open-source **frontend-design** skill on first run (needs internet once) and caches it under `skills/frontend-design/SKILL.md`.

## Running

```bash
python strands-agents/01_basic_agent.py
```

Each file is self-contained and runnable independently.
