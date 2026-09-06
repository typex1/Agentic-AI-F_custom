"""
02a_chat_agent_internet_search.py — Chat agent with tools + internet search
(Strands + Nova Lite)

A copy of 02_chat_agent_tools.py extended with internet search
(task: tasks/02a_chat_agent_internet_search.md):
  - Custom `web_search` tool using DDGS (DuckDuckGo Search).
  - `bash` (vended by strands-agents) plus `file_read`, `file_write`
    from `strands_tools`.
  - The agent decides on its own when a user request needs a tool
    (e.g., "search the web for X", "read README.md", "list the files here").
  - User prompts are read from the terminal; conversation history is kept.

NOTE: `bash` replaces the deprecated `shell` tool (removed in
strands-agents-tools v0.9.0) and executes WITHOUT a confirmation prompt.
`file_write` still asks for confirmation; set BYPASS_TOOL_CONSENT=true
to skip that (e.g., for unattended runs).

Run:
  python 02a_chat_agent_internet_search.py

Exit with "exit", "quit", or Ctrl-D.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from datetime import date

from ddgs import DDGS
from strands import Agent, tool
from strands.vended_tools import bash
from strands_tools import file_read, file_write


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
        "You have tools to run bash commands, read and write files, and "
        "search the internet; use them whenever a request requires "
        "interacting with the system or up-to-date information from the web."
    ),
    tools=[bash, file_read, file_write, web_search],
    callback_handler=None,  # suppress streaming; we print the final result
)


def main() -> None:
    print("Chat agent with tools: bash, file_read, file_write, web_search (Nova Lite).")
    print("Type 'exit' or Ctrl-D to quit.\n")
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

        response = agent(user_input)
        print(f"Bot: {response}\n")

    print("Goodbye!")


if __name__ == "__main__":
    main()
