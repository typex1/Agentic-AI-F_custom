# MCP Tools

**Python file:** [`../05_mcp_tools.py`](../05_mcp_tools.py)

## Learning objective
Give an agent access to tools hosted by an external Model Context Protocol (MCP)
server, rather than only locally-defined Python tools.

## Why it matters
MCP is the emerging standard for connecting agents to external tools and data.
It lets you reuse existing servers and expose capabilities across many clients
without re-implementing them per framework.

## What this example demonstrates
- Connecting to a remote MCP server (the public **AWS Knowledge MCP server**)
  over Streamable HTTP with `MCPClient` + `streamablehttp_client`.
- Discovering the server's tools with `list_tools_sync()` and handing them to an
  agent.
- The agent autonomously using MCP tools to answer AWS questions (with
  citations), plus **direct** MCP tool invocation with `call_tool_sync`.
- Managing the MCP connection lifecycle with a context manager.

## Key concepts
`MCPClient`, Streamable HTTP transport, tool discovery, tool-name prefixes
(`aws___...`), direct MCP tool invocation.
