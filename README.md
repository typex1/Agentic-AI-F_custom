# Agentic AI — Custom Agents with the Strands Agents SDK

A structured, hands-on learning path for building custom AI agents using the **[Strands Agents SDK](https://strandsagents.com/)** on **Amazon Bedrock**.

From "Hello World" to multi-agent swarms, RAG pipelines, and production deployment — all runnable with a single model permission (`bedrock-runtime:Converse`).

## 🗺️ Learning Path

```
┌─────────────────────────────────────────────────────────────────────────┐
│  01-fundamentals   →   02-tools-and-mcp   →   03-advanced-patterns     │
│  (basics, tools,       (MCP servers,           (RAG, multi-agent,       │
│   logging, output)      agent skills)           graphs, swarms)         │
│                                                                         │
│                    →   04-production       →   05-evaluation            │
│                        (sessions, context       (testing, quality)       │
│                         management)                                      │
└─────────────────────────────────────────────────────────────────────────┘
         exercises/  — hands-on practice with guided tasks
         reference/  — full 14-module video course + official samples
```

## 📚 Modules

| Module | Topic | Scripts |
|--------|-------|---------|
| [01-fundamentals](01-fundamentals/) | Agent basics, custom tools, logging, structured output | 5 files |
| [02-tools-and-mcp](02-tools-and-mcp/) | MCP integration, agent skills | 2 files |
| [03-advanced-patterns](03-advanced-patterns/) | RAG, multi-agent, graphs, swarms | 5 files |
| [04-production](04-production/) | Session persistence, conversation management | 2 files |
| [05-evaluation](05-evaluation/) | Agent evaluation techniques and reports | reports |

## 🏋️ Exercises

| Exercise | Description |
|----------|-------------|
| [Customer Support Tickets](exercises/Customer-Support-Tickets/) | All four workflow patterns in one project |
| [Task Sheets](exercises/tasks/) | Incremental guided tasks (01–05) |
| [Lab 2](exercises/Lab-2/) | Jupyter notebook exploration |

## 📖 Reference

| Resource | Description |
|----------|-------------|
| [Building with Strands Course](reference/building-with-strands-course/) | 14-module video course (Morgan Willis, AWS) |
| [Official Strands Examples](reference/strands-official-examples/) | Samples from the strands-agents repo |

## 🆚 Framework Comparison

| Framework | Emphasis | Docs |
|-----------|----------|------|
| **Strands Agents** (primary) | AWS-native, Bedrock, AgentCore | [strands-vs-pydantic](docs/strands-vs-pydantic.md) |
| **Pydantic AI** (comparison) | Type-safety, DI, FastAPI-style | [pydantic-ai/](pydantic-ai/) |

## 🚀 Quick Start

```bash
git clone https://github.com/typex1/Agentic-AI-F_custom.git
cd Agentic-AI-F_custom

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run your first agent:
python 01-fundamentals/01_basic_agent.py
```

→ Full setup details: [docs/setup.md](docs/setup.md)

## 🔧 Environment

| Component | Value |
|-----------|-------|
| Model | Amazon Nova Lite (`amazon.nova-lite-v1:0`) |
| Region | `us-east-1` |
| Permission | `bedrock-runtime:Converse` (+ related actions) |
| SDK | `strands-agents` 1.45.0 |
| Tools | `strands-agents-tools` 0.8.2 |

> **Note:** All scripts work with the minimal Bedrock runtime permission.
> See [docs/model-permissions.md](docs/model-permissions.md) for the full verified matrix.

## 📦 Dependencies

See [`requirements.txt`](requirements.txt) for pinned versions. Key packages:

| Package | Used in |
|---------|---------|
| `strands-agents` | All modules |
| `strands-agents-tools` | Modules 01–04 |
| `pydantic` | Structured output (Module 01) |
| `mcp` | MCP tools (Module 02) |
| `strands-agents-evals` | Evaluation (Module 05, reference) |
| `pydantic-ai-slim[bedrock]` | Pydantic AI comparison |

## 🔗 Links

- [Strands Agents Homepage](https://strandsagents.com)
- [Strands Agents Documentation](https://strandsagents.com/docs/user-guide/quickstart/python/)
- [Strands Agents GitHub](https://github.com/strands-agents/sdk-python)
- [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
- [Building with Strands Course (YouTube)](https://www.youtube.com/playlist?list=PLDzwjhH-4yhU)
- [Hands-on Workshop (AWS)](https://catalog.us-east-1.prod.workshops.aws/workshops/083b80d7-5a90-402b-9bb4-19fb53092808/en-US)
