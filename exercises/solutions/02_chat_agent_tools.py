"""
02_chat_agent_tools.py — Interactive chat agent with built-in tools (Strands + Nova Lite)

A copy of 01_chat_agent.py extended with tool calling:
  - `bash` (vended by strands-agents) plus `file_read`, `file_write`
    from `strands_tools`.
  - The agent decides on its own when a user request needs a tool
    (e.g., "list the files here", "read README.md", "save that to notes.txt").
  - User prompts are read from the terminal; conversation history is kept.

NOTE: `bash` replaces the deprecated `shell` tool (removed as an error in
strands-agents-tools v0.9.0). Unlike `shell`, `bash` executes immediately
WITHOUT a confirmation prompt. `file_write` still asks for confirmation;
set BYPASS_TOOL_CONSENT=true to skip that (e.g., for unattended runs).

Run:
  python 02_chat_agent_tools.py

Exit with "exit", "quit", or Ctrl-D.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent
from strands.vended_tools import bash
from strands_tools import file_read, file_write

agent = Agent(
    model="amazon.nova-lite-v1:0",  # the only model permitted in this environment
    system_prompt=(
        "You are a friendly, helpful chatbot. "
        "Answer the user's questions clearly and concisely. "
        "You have tools to run bash commands and to read and write files; "
        "use them whenever a request requires interacting with the system."
    ),
    tools=[bash, file_read, file_write],
    callback_handler=None,  # suppress streaming; we print the final result
)


def main() -> None:
    print("Chat agent with tools: bash, file_read, file_write (Nova Lite).")
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
