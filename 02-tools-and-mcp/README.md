# Module 2: Tools & MCP

Extend your agents with external capabilities — MCP (Model Context Protocol) servers and community skills.

## Learning Path

| # | File | Concept | What you'll learn |
|---|------|---------|-------------------|
| 5 | `05_mcp_tools.py` | MCP integration | Consume tools from external MCP servers (AWS Knowledge MCP) |
| 6 | `06_agent-skill.py` | Agent Skills | Load and use community skills (Anthropic's frontend-design skill) |

## Prerequisites

```bash
pip install strands-agents strands-agents-tools
# MCP server needs uv/uvx:
./0-install.sh
```

## Running

```bash
python 02-tools-and-mcp/05_mcp_tools.py
python 02-tools-and-mcp/06_agent-skill.py
```

## Key Concepts

### MCP (Model Context Protocol)

MCP lets agents consume tools from external servers over a standard protocol. The agent doesn't need to know the tool's implementation — it just discovers and calls it.

```python
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client

mcp = MCPClient(lambda: stdio_client("uvx", ["strands-agents-mcp-server"]))
agent = Agent(tools=[mcp])
```

### Agent Skills

Skills are reusable prompt+tool bundles. `06_agent-skill.py` demonstrates loading Anthropic's open-source **frontend-design** skill, which gets cached locally under `skills/frontend-design/SKILL.md`.

## External Resources

- [AWS Knowledge MCP Server](https://knowledge-mcp.global.api.aws) — public, no auth needed
- [Strands MCP docs](https://strandsagents.com/docs/user-guide/concepts/tools/mcp-tools/)
- [MCP specification](https://modelcontextprotocol.io/)
