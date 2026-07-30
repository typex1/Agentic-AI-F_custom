"""
01_chat_agent.py — Simple interactive chat agent (Strands + Amazon Nova Lite)

A minimal chatbot:
  - The agent has a system prompt defined in code.
  - User prompts are NOT hardcoded; they are read from the terminal.
  - The Strands Agent keeps the conversation history, so follow-up
    questions work naturally.

Run:
  python 01_chat_agent.py

Exit with "exit", "quit", or Ctrl-D.

Example prompts:
You: How many days are in a year?
Bot: There are 365 days in a common year, and 366 days in a leap year.

This will check if "context memory" works:
You: And in ten years?
Bot: In 10 common years, there are 3650 days. In 10 years with 2 leap years, there are 3652 days.


You: Name the top ten contemporary US writers.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent

agent = Agent(
    model="amazon.nova-lite-v1:0",  # the only model permitted in this environment
    system_prompt=(
        "You are a friendly, helpful chatbot. "
        "Answer the user's questions clearly and concisely."
    ),
    callback_handler=None,  # suppress streaming; we print the final result
)


def main() -> None:
    print("Simple chat agent (Nova Lite). Type 'exit' or Ctrl-D to quit.\n")
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
