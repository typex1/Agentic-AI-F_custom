"""
02_chat_agent_tools.py — Interactive chat agent with built-in tools (Strands + Nova Lite)

A copy of 01_chat_agent.py extended with tool calling:
  - Built-in tools from `strands_tools`: shell, file_read, file_write.
  - The agent decides on its own when a user request needs a tool
    (e.g., "list the files here", "read README.md", "save that to notes.txt").
  - User prompts are read from the terminal; conversation history is kept.

NOTE: `shell` and `file_write` perform real system actions, so they ask for
human confirmation before executing. Set BYPASS_TOOL_CONSENT=true in the
environment to skip those prompts (e.g., for unattended runs).

Run:
  python 02_chat_agent_tools.py

Exit with "exit", "quit", or Ctrl-D.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent
from strands_tools import file_read, file_write, shell

agent = Agent(
    model="amazon.nova-lite-v1:0",  # the only model permitted in this environment
    system_prompt=(
        "You are a friendly, helpful chatbot. "
        "Answer the user's questions clearly and concisely. "
        "You have tools to run shell commands and to read and write files; "
        "use them whenever a request requires interacting with the system."
    ),
    tools=[shell, file_read, file_write],
    callback_handler=None,  # suppress streaming; we print the final result
)


def main() -> None:
    print("Chat agent with tools: shell, file_read, file_write (Nova Lite).")
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
