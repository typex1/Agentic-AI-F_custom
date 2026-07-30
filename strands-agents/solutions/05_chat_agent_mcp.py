"""
05_chat_agent_mcp.py — Chat agent with tools, internet search, logging + MCP
(Strands + Nova Lite)

A copy of 03_chat_agent_logging.py extended with the AWS Knowledge MCP server:
  - Connects to https://knowledge-mcp.global.api.aws (remote, Streamable HTTP,
    public, no authentication, rate-limited).
  - Lists the tools the MCP server provides before starting the chat.
  - The MCP tools (search/read AWS docs, list regions, ...) are added to the
    agent alongside the local tools, so the agent can answer AWS questions
    from official documentation.
  - Each tool call is shown in the terminal (🔧 [tool called: ...]) so you
    can see which tool or MCP tool the agent chose for each question.
  - Every user prompt, agent response, and tool call is logged to
        /tmp/05_chat_agent_mcp.log
    Follow it in a second terminal with:
        tail -f /tmp/05_chat_agent_mcp.log

NOTE: `shell` and `file_write` perform real system actions, so they ask for
human confirmation before executing. Set BYPASS_TOOL_CONSENT=true in the
environment to skip those prompts (e.g., for unattended runs).

Run:
  python 05_chat_agent_mcp.py

Exit with "exit", "quit", or Ctrl-D.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import json
import logging
from datetime import date
from pathlib import Path

from ddgs import DDGS
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent, tool
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AfterToolCallEvent, BeforeToolCallEvent
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write, shell

# --- Logging setup: file under /tmp, fresh on every run -----------------------
LOG_FILE = Path("/tmp/05_chat_agent_mcp.log")
LOG_FILE.unlink(missing_ok=True)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")],
)

# Keep the framework and noisy third-party libraries quiet so our own
# lines (chat turns + tool calls) stand out in the log.
logging.getLogger("strands").setLevel(logging.WARNING)
for noisy in ("botocore", "boto3", "urllib3", "ddgs", "httpx", "mcp"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger("chat_agent")
logger.setLevel(logging.INFO)


# --- Hook: log each tool invocation --------------------------------------------
# BeforeToolCallEvent fires just before a tool runs (the tool the model picked
# and the arguments it passed); AfterToolCallEvent fires when it completes
# (result status). Hooks are a documented public API, so this keeps working
# across SDK upgrades — unlike tapping SDK-internal logger names.
class ToolUseLogger(HookProvider):
    """Logs each tool the model picks, its arguments, and its result status.

    Also prints the tool name to the terminal, so students can see which
    (MCP) tool the agent chose for each question.
    """

    def __init__(self, log: logging.Logger):
        self._log = log

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)

    def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        name = event.tool_use["name"]
        kind = "MCP tool" if name.startswith("aws___") else "tool"
        print(f"    🔧 [{kind} called: {name}]")
        self._log.info(
            "TOOL CALL | tool=%s | input=%s",
            name,
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


# --- MCP: AWS Knowledge MCP server (remote, Streamable HTTP, no auth) ---------
AWS_KNOWLEDGE_MCP_URL = "https://knowledge-mcp.global.api.aws"

aws_knowledge_client = MCPClient(
    lambda: streamablehttp_client(AWS_KNOWLEDGE_MCP_URL)
)


def main() -> None:
    # MCP connections must be used within a context manager; the connection
    # stays open for the whole chat session.
    with aws_knowledge_client:
        # --- List the tools the MCP server provides, before starting the chat
        mcp_tools = aws_knowledge_client.list_tools_sync()
        print("=== Tools available from the AWS Knowledge MCP server ===")
        for t in mcp_tools:
            print(f"  • {t.tool_name}")
        print()
        logger.info(
            "MCP SERVER | url=%s | tools=%s",
            AWS_KNOWLEDGE_MCP_URL,
            ", ".join(t.tool_name for t in mcp_tools),
        )

        agent = Agent(
            model="amazon.nova-lite-v1:0",  # the only model permitted here
            system_prompt=(
                "You are a friendly, helpful chatbot. "
                "Answer the user's questions clearly and concisely. "
                "You have tools to run shell commands, read and write files, "
                "and search the internet; use them whenever a request requires "
                "interacting with the system or up-to-date information from "
                "the web. For questions about AWS services or documentation, "
                "prefer the AWS Knowledge tools, which search and read the "
                "official AWS docs."
            ),
            tools=[shell, file_read, file_write, web_search, *mcp_tools],
            hooks=[ToolUseLogger(logger)],  # log every tool call + result
            callback_handler=None,  # suppress streaming; we print final result
        )

        print("Chat agent with local tools (shell, file_read, file_write, "
              "web_search)\nplus the AWS Knowledge MCP tools above (Nova Lite).")
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
