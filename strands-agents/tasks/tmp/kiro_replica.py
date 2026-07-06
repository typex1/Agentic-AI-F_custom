"""
kiro_replica.py — Minimal Kiro-CLI Replica

A REPL-style interactive coding assistant powered by Amazon Nova Lite
via Strands Agents SDK. Equipped with shell and web_search tools.
"""

import os
import sys
import warnings

warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

# Allow shell tool to run without confirmation prompts for demo purposes.
# In production, remove this to require human approval for each command.
os.environ["BYPASS_TOOL_CONSENT"] = "true"

from strands import Agent, tool
from strands_tools import shell
from ddgs import DDGS


# --- Custom callback handler for streaming output ---
_tool_calls_seen = []


def callback_handler(**kwargs):
    """Stream tokens and tool-call indicators to the terminal in real time."""
    if "data" in kwargs:
        print(kwargs["data"], end="", flush=True)

    elif "current_tool_use" in kwargs:
        tool_info = kwargs["current_tool_use"]
        tool_id = tool_info.get("toolUseId", "")
        tool_name = tool_info.get("name", "")

        if tool_name and tool_id not in _tool_calls_seen:
            _tool_calls_seen.append(tool_id)
            print(f"\n  🔧 [{tool_name}]", flush=True)

    elif "complete" in kwargs:
        print()  # newline after response


# --- Web search tool using DuckDuckGo ---
@tool
def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using DuckDuckGo and return results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default: 3).

    Returns:
        Search results with titles, URLs, and snippets.
    """
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        output = []
        for r in results:
            output.append(f"• {r['title']}\n  {r['href']}\n  {r['body']}")
        return "\n\n".join(output)
    except Exception as e:
        return f"Search error: {e}"


# --- System prompt ---
SYSTEM_PROMPT = """\
You are Kiro, a helpful AI coding assistant running in the user's terminal.
You have access to two tools:
- shell: Execute shell commands on the local machine to answer questions about \
files, system state, processes, etc.
- web_search: Search the internet for current information, documentation, \
latest versions, news, etc.

Be concise and direct. Use tools when the question requires real system \
information or up-to-date external knowledge. Always prefer to act (run a \
command or search) rather than guess."""


def print_banner():
    """Print a startup banner."""
    print("\n╔══════════════════════════════════════════╗")
    print("║   Kiro CLI Replica (Nova Lite + Strands) ║")
    print("╠══════════════════════════════════════════╣")
    print("║  Tools: shell, web_search                ║")
    print("║  Type 'exit' or 'quit' to leave          ║")
    print("║  Type '/help' for commands               ║")
    print("╚══════════════════════════════════════════╝\n")


def print_help():
    """Print help text."""
    print("\nAvailable commands:")
    print("  exit, quit   — End the session")
    print("  /help        — Show this help message")
    print("  Ctrl+D       — End the session")
    print("  Anything else is sent to the agent.\n")


def main():
    """Run the interactive REPL loop."""
    print_banner()

    # Create the agent — reuse across turns to preserve conversation history
    agent = Agent(
        model="amazon.nova-lite-v1:0",
        tools=[shell, web_search],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=callback_handler,
    )

    while True:
        _tool_calls_seen.clear()

        try:
            user_input = input("\033[1;36mkiro>\033[0m ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        # Strip whitespace
        user_input = user_input.strip()

        # Skip empty input
        if not user_input:
            continue

        # Exit commands
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        # Help command
        if user_input.lower() == "/help":
            print_help()
            continue

        # Send to agent
        try:
            agent(user_input)
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
