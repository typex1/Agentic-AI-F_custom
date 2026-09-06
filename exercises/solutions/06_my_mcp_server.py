"""
06_my_mcp_server.py — A minimal MCP server built with FastMCP

Solution (part 1 of 2) for exercises/tasks/06_build_your_own_mcp_server.md.
Exposes two tools over stdio transport. Started as a subprocess by
06_agent_with_my_mcp_server.py — you don't run it directly (it would just
wait on stdin).
"""

import random
from datetime import datetime
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP

server = FastMCP("my-first-mcp-server")


@server.tool()
def current_time(timezone: str = "UTC") -> str:
    """Return the current date and time in the given IANA timezone,
    e.g. 'Europe/Berlin' or 'UTC'."""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except Exception:
        return f"Unknown timezone: {timezone!r}. Use an IANA name like 'Europe/Berlin'."
    return now.strftime(f"%Y-%m-%d %H:%M:%S ({timezone})")


@server.tool()
def dice_roll(sides: int = 6) -> int:
    """Roll a fair die with the given number of sides and return the result."""
    if sides < 2:
        raise ValueError("A die needs at least 2 sides.")
    return random.randint(1, sides)


if __name__ == "__main__":
    server.run()  # stdio transport
