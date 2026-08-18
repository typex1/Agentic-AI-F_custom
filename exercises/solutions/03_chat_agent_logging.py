"""
03_chat_agent_logging.py — Chat agent with tools, internet search, and logging
(Strands + Nova Lite)

A copy of 02a_chat_agent_internet_search.py extended with logging:
  - Every user prompt and final agent response is logged.
  - Every tool call (tool name + arguments) and its result status is logged
    via the public Strands hooks API (BeforeToolCallEvent /
    AfterToolCallEvent) — the same approach as strands-agents/03_logging.py.
  - The log file lives under /tmp and is truncated on every run:
        /tmp/03_chat_agent_logging.log
    Follow it in a second terminal with:
        tail -f /tmp/03_chat_agent_logging.log

NOTE: `shell` and `file_write` perform real system actions, so they ask for
human confirmation before executing. Set BYPASS_TOOL_CONSENT=true in the
environment to skip those prompts (e.g., for unattended runs).

Run:
  python 03_chat_agent_logging.py

Exit with "exit", "quit", or Ctrl-D.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import json
import logging
from datetime import date
from pathlib import Path

from ddgs import DDGS
from strands import Agent, tool
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AfterToolCallEvent, BeforeToolCallEvent
from strands_tools import file_read, file_write, shell

# --- Logging setup: file under /tmp, fresh on every run -----------------------
LOG_FILE = Path("/tmp/03_chat_agent_logging.log")
LOG_FILE.unlink(missing_ok=True)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")],
)

# Keep the framework and noisy third-party libraries quiet so our own
# lines (chat turns + tool calls) stand out in the log.
logging.getLogger("strands").setLevel(logging.WARNING)
for noisy in ("botocore", "boto3", "urllib3", "ddgs"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger("chat_agent")
logger.setLevel(logging.INFO)


# --- Hook: log each tool invocation --------------------------------------------
# BeforeToolCallEvent fires just before a tool runs (the tool the model picked
# and the arguments it passed); AfterToolCallEvent fires when it completes
# (result status). Hooks are a documented public API, so this keeps working
# across SDK upgrades — unlike tapping SDK-internal logger names.
class ToolUseLogger(HookProvider):
    """Logs each tool the model picks, its arguments, and its result status."""

    def __init__(self, log: logging.Logger):
        self._log = log

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)

    def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        self._log.info(
            "TOOL CALL | tool=%s | input=%s",
            event.tool_use["name"],
            json.dumps(event.tool_use.get("input", {}), default=str),
        )

    def _on_after_tool_call(self, event: AfterToolCallEvent) -> None:
        self._log.info(
            "TOOL RESULT | tool=%s | status=%s",
            event.tool_use["name"],
            event.result.get("status"),
        )


# --- Custom tool: internet search via DuckDuckGo (ddgs) ---
@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the internet using DuckDuckGo and return live, current results.

    Returns two labeled sections: results from the past year (most useful
    for questions about 'latest', 'newest', or 'current' things) and
    general results. Trust these results over memorized knowledge for
    time-sensitive questions; if they are inconclusive, search again with
    more specific terms.

    Args:
        query: The search query string. Supports search operators such as
            site:example.com, filetype:pdf, -term (exclude), and
            "exact phrase".
        max_results: Maximum number of results per section (default: 5).

    Returns:
        The retrieval date followed by the two sections of search results
        with titles, URLs, and snippets.
    """
    def _format(results):
        return "\n\n".join(
            f"• {r['title']}\n  {r['href']}\n  {r['body']}" for r in results
        )

    try:
        recent = DDGS().text(query, max_results=max_results, timelimit="y")
        general = DDGS().text(query, max_results=max_results)
        if not recent and not general:
            return "No results found."
        today = date.today().isoformat()
        output = [f"Web search results for '{query}', retrieved {today}."]
        if recent:
            output.append("--- Results from the past year ---\n\n" + _format(recent))
        if general:
            output.append("--- General results (any date) ---\n\n" + _format(general))
        return "\n\n".join(output)
    except Exception as e:
        return f"Search error: {e}"


agent = Agent(
    model="amazon.nova-lite-v1:0",  # the only model permitted in this environment
    system_prompt=(
        "You are a friendly, helpful chatbot. "
        "Answer the user's questions clearly and concisely. "
        "You have tools to run shell commands, read and write files, and "
        "search the internet; use them whenever a request requires "
        "interacting with the system or up-to-date information from the web."
    ),
    tools=[shell, file_read, file_write, web_search],
    hooks=[ToolUseLogger(logger)],  # log every tool call + result
    callback_handler=None,  # suppress streaming; we print the final result
)


def main() -> None:
    print("Chat agent with tools: shell, file_read, file_write, web_search (Nova Lite).")
    print(f"Logging to: {LOG_FILE}")
    print("Type 'exit' or Ctrl-D to quit.\n")
    logger.info("SESSION START | model=amazon.nova-lite-v1:0 | tools=%s",
                ", ".join(agent.tool_names))
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        logger.info("USER PROMPT | %s", user_input)
        response = agent(user_input)
        logger.info("AGENT RESPONSE | %s", str(response).strip())
        print(f"Bot: {response}\n")

    logger.info("SESSION END")
    print("Goodbye!")


if __name__ == "__main__":
    main()
