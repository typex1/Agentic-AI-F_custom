# Task: build your own MCP server

In task 05 you *consumed* an existing MCP server. Now switch sides and
*produce* one — then connect your agent to it.

1. Write a minimal MCP server with **FastMCP** (`mcp` package, already in
   `requirements.txt`). ~30 lines are enough:
   - `from mcp.server.fastmcp import FastMCP`, create `FastMCP("my-server")`
   - expose two tools with `@server.tool()`, e.g.
     `current_time(timezone: str) -> str` and
     `dice_roll(sides: int = 6) -> int` — or invent your own
   - end with `server.run()` (stdio transport)
2. Connect your chat agent from task 05 to it as a **local stdio server**:
   the client launches your server as a subprocess
   (`StdioServerParameters(command=sys.executable, args=["my_mcp_server.py"])`).
3. Ask the agent something that requires *your* tool and verify in the
   output that it was called.
4. Bonus: also keep the remote AWS Knowledge MCP server connected — your
   agent now uses tools from two MCP servers at once.

Hint: an `MCPClient` is a context manager; keep the `with` block open for the
whole chat loop, and pass the *tool list* (`list_tools_sync()`) to the agent.

## 📖 Official documentation

- [MCP Tools](https://strandsagents.com/docs/user-guide/concepts/tools/mcp-tools/) — stdio transport & `MCPClient`
- [MCP: Build a server](https://modelcontextprotocol.io/docs/develop/build-server) — the FastMCP quickstart
