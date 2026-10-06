# Agentic AI — Custom Agents with the Strands Agents SDK

A structured, hands-on learning path for building custom AI agents using the **[Strands Agents SDK](https://strandsagents.com/)** on **Amazon Bedrock**.

## 📖 Reference

| Resource | Description |
|----------|-------------|
| [Building with Strands Course](reference/building-with-strands-course/) | 14-module video course (Morgan Willis, AWS) |
| [Official Strands Examples](reference/strands-official-examples/) | Samples from the strands-agents repo |
| [Agent Loop visualized](Agent-Loop/) | Mermaid diagrams of the Strands agent loop and its concrete example |

## 🆚 Framework Comparison

| Framework | Emphasis | Docs |
|-----------|----------|------|
| **Strands Agents** (primary) | AWS-native, Bedrock, AgentCore | [strands-vs-pydantic](docs/strands-vs-pydantic.md) |
| **Pydantic AI** (comparison) | Type-safety, DI, FastAPI-style | [pydantic-ai/](pydantic-ai/) |

## 🚀 Quick Start

```bash
git clone https://github.com/typex1/Agentic-AI-F_custom.git
cd Agentic-AI-F_custom

# Install uv (needed to run MCP servers via uvx in Module 02):
curl -LsSf https://astral.sh/uv/install.sh | sh

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Kiro
curl -fsSL https://cli.kiro.dev/install | bash

# Log into your Kiro account:
kiro-cli login --use-device-flow
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
