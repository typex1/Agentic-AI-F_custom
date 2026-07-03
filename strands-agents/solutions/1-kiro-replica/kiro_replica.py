"""
kiro_replica.py — A minimal Kiro-CLI replica (reference solution for Task 1)

A stripped-down interactive coding assistant built on the Strands Agents SDK.

Required feature set (and nothing more):
  - Backed by Amazon Nova Lite (amazon.nova-lite-v1:0) on Amazon Bedrock.
  - Can run shell commands on the local machine.
  - Can perform an internet search.

The agent runs the full agentic loop itself:
  Input -> Reasoning (Nova Lite) -> Tool selection -> Tool execution -> Response

Design notes:
  - A single Agent instance is reused across turns, so it keeps the
    conversation history for the whole session.
  - A streaming callback_handler prints tokens as they arrive and shows a small
    indicator whenever a tool fires, which makes it feel like the real CLI.
  - Shell access is powerful and dangerous. By default this solution asks the
    human to approve every command (the strands_tools `shell` tool prompts for
    consent). Pass --yolo to bypass that for an unattended demo.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import os
import sys

from strands import Agent, tool
from strands_tools import shell
from ddgs import DDGS


MODEL_ID = "amazon.nova-lite-v1:0"  # the only model we have access to here

SYSTEM_PROMPT = (
    "You are Kiro-Replica, a concise command-line coding assistant running in "
    "the user's terminal.\n"
    "You have two tools:\n"
    "  - shell: run shell commands on the user's local machine. Use it to "
    "inspect files, run programs, check the environment, etc.\n"
    "  - web_search: search the internet for current or external information "
    "you do not already know.\n"
    "Decide for yourself when a tool is needed. Prefer the shell for anything "
    "about the local system, and web_search for anything about the outside "
    "world or recent events. When you run a command, base your answer on its "
    "actual output. Keep responses short and to the point."
)


# --- Web search tool (DuckDuckGo via ddgs), same pattern as demo 02 ---
@tool
def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using DuckDuckGo and return results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default: 3).

    Returns:
        Search results with titles, URLs, and snippets, or an error message.
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


# --- Streaming callback: live tokens + a small indicator when a tool fires ---
_tools_seen = set()


def streaming_handler(**kwargs):
    """Print model tokens as they stream and flag tool invocations."""
    if "data" in kwargs:
        print(kwargs["data"], end="", flush=True)
    elif "current_tool_use" in kwargs:
        info = kwargs["current_tool_use"]
        tool_id = info.get("toolUseId", "")
        tool_name = info.get("name", "")
        if tool_name and tool_id and tool_id not in _tools_seen:
            _tools_seen.add(tool_id)
            print(f"\n  🔧 [{tool_name}]", flush=True)


BANNER = r"""
┌─────────────────────────────────────────────┐
│  Kiro-Replica CLI  ·  Nova Lite + shell/web  │
└─────────────────────────────────────────────┘
Type your request. Commands: /help, exit (or quit, Ctrl-D).
"""

HELP = """
Kiro-Replica — a minimal coding assistant.
  • Ask it about your local system  → it runs shell commands.
  • Ask it about the outside world   → it searches the web.
  • It remembers the conversation for this session.

Commands:
  /help        Show this help.
  exit, quit   Leave the session (Ctrl-D also works).
"""


def build_agent() -> Agent:
    """Create the Nova Lite agent with the shell and web_search tools."""
    return Agent(
        model=MODEL_ID,
        tools=[shell, web_search],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=streaming_handler,
    )


def repl(agent: Agent) -> None:
    """Run the interactive read-eval-print loop."""
    print(BANNER)
    while True:
        try:
            user_input = input("\nkiro> ").strip()
        except EOFError:            # Ctrl-D
            print("\nBye.")
            break
        except KeyboardInterrupt:   # Ctrl-C: cancel current line, stay in loop
            print("\n(interrupted — type 'exit' to quit)")
            continue

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Bye.")
            break
        if user_input == "/help":
            print(HELP)
            continue

        # Reset the per-turn tool indicator set, then let the agent run its loop.
        _tools_seen.clear()
        try:
            agent(user_input)
            print()  # newline after the streamed response
        except Exception as e:
            # A failed tool or model call should not kill the session.
            print(f"\n[error] {e}")


def main() -> None:
    # Shell access is dangerous. Default to human-in-the-loop confirmation;
    # allow an explicit opt-out for unattended demos.
    if "--yolo" in sys.argv:
        os.environ["BYPASS_TOOL_CONSENT"] = "true"
        print("[warning] --yolo: shell commands will run WITHOUT confirmation.")

    repl(build_agent())


if __name__ == "__main__":
    main()
