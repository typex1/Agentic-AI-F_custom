# Agentic-AI-F_custom

Kiro CLI installation:
```
curl -fsSL https://cli.kiro.dev/install | bash
kiro-cli login --use-device-flow
```

Install "tree" command (optional):
```
sudo yum install tree -y
```

## Workspace Overview

Exploration of AI agent frameworks — primarily the **Strands Agents SDK**, with
a **Pydantic AI** comparison — running on **Amazon Bedrock** with the
**Amazon Nova Lite** model (`amazon.nova-lite-v1:0`) in `us-east-1`.

> **Permissions note:** This environment only permits `bedrock-runtime:Converse`
> (and the other `bedrock-runtime` actions) on Nova Lite. It has **no** Bedrock
> control-plane or other AWS service access. See
> [`.kiro/steering/Permissions.md`](.kiro/steering/Permissions.md) and
> [`Model_permissions.md`](Model_permissions.md) for the verified details.

## Contents

| Path | Description |
|------|-------------|
| `Task.py` | Python extracted from `Task.ipynb` (first-agent tutorial), task-labeled |
| `Model_permissions.py` / `.md` | Probes + summary of which Bedrock actions are permitted |
| `strands-agents/` | Strands Agents SDK demos (see its own `README.md`) |
| `pydantic-ai/` | Pydantic AI equivalents for comparison |
| `StrandsAgents_vs_PydanticAI.md` | Framework comparison writeup |
| `0-install.sh` | Installs `Python dependencies and non-pip tools |
| `requirements.txt` | Pinned Python dependencies |

## Setup

```bash
# Python dependencies and non-pip tools (uv/uvx, used by the MCP server config)
./0-install.sh          # installs uv / uvx
```

All example scripts are runnable from any working directory.

## Dependencies

Pinned in [`requirements.txt`](requirements.txt) to the versions verified in
this environment:

| Package | Version | Used by |
|---------|---------|---------|
| `strands-agents` | 1.45.0 | all `strands-agents` demos, `Task.py` |
| `strands-agents-tools` | 0.8.2 | current_time / calculator / shell / file_read tools (demos 02, 03, 06) |
| `ddgs` | 9.14.4 | web search (demo 02, `Task.py`) |
| `pydantic` | 2.13.4 | structured output (demo 04) |
| `boto3` | 1.43.39 | `Model_permissions.py` |
| `pydantic-ai-slim[bedrock]` | 2.3.0 | `pydantic-ai/01_basic_agent.py` |

**Not pip-installable** (installed separately):

| Tool | How | Used by |
|------|-----|---------|
| `uv` / `uvx` | `0-install.sh` (`curl -LsSf https://astral.sh/uv/install.sh \| sh`) | MCP server (`uvx strands-agents-mcp-server`) |

## MCP servers configured

`.kiro/settings/mcp.json` registers the **Strands Agents MCP server**
(`uvx strands-agents-mcp-server`), giving AI coding assistants direct access to
the Strands documentation.
