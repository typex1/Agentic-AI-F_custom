"""
06_agent_with_my_mcp_server.py — Agent connected to YOUR OWN MCP server

Solution (part 2 of 2) for exercises/tasks/06_build_your_own_mcp_server.md:
  - Launches 06_my_mcp_server.py as a local stdio MCP server (subprocess).
  - Lists the discovered tools, then lets the agent use them.
  - Non-interactive demo: asks two questions that require the custom tools.

Run:
  python 06_agent_with_my_mcp_server.py
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import sys
from pathlib import Path

from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.tools.mcp import MCPClient

SERVER_SCRIPT = Path(__file__).parent / "06_my_mcp_server.py"

# The client LAUNCHES the server as a subprocess and talks to it over stdio.
my_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command=sys.executable, args=[str(SERVER_SCRIPT)])
    )
)

with my_mcp_client:  # connection lifetime = tool lifetime
    tools = my_mcp_client.list_tools_sync()
    print("=== Tools discovered from MY MCP server ===")
    for t in tools:
        print(f"  • {t.tool_name}")
    print()

    agent = Agent(
        model="amazon.nova-lite-v1:0",  # the only model permitted in this environment
        system_prompt=(
            "You are a helpful assistant. Use your tools whenever a question "
            "requires the current time or rolling dice."
        ),
        tools=tools,
        callback_handler=None,
    )

    print("Q: What time is it right now in Berlin?")
    print(f"A: {agent('What time is it right now in Berlin? Use your tool.')}\n")

    print("Q: Roll a 20-sided die for me.")
    print(f"A: {agent('Roll a 20-sided die for me.')}")
