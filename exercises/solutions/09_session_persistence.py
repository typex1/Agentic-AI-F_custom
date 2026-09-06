"""
09_session_persistence.py — Chat agent that survives a restart (Strands + Nova Lite)

Solution for exercises/tasks/09_session_persistence.md:
  - FileSessionManager stores the conversation under /tmp/strands_sessions.
  - A fixed session id means: run the script, tell it facts, exit, run it
    again — the agent still knows them.
  - --new starts a fresh conversation (new UUID session id).

Run:
  python 09_session_persistence.py           # resumes session "student"
  python 09_session_persistence.py --new     # starts a fresh session

Try: tell the agent your name, exit, restart, ask "What is my name?"
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import sys
import uuid
from pathlib import Path

from strands import Agent
from strands.session import FileSessionManager

STORAGE_DIR = Path("/tmp/strands_sessions")


def main() -> None:
    if "--new" in sys.argv:
        session_id = str(uuid.uuid4())
        print(f"Starting a FRESH session: {session_id}")
    else:
        session_id = "student"
        print('Resuming session "student" (use --new for a fresh one).')
    print(f"Session storage: {STORAGE_DIR}\n")

    agent = Agent(
        model="amazon.nova-lite-v1:0",  # the only model permitted in this environment
        system_prompt=(
            "You are a friendly chatbot. Remember details the user tells you."
        ),
        session_manager=FileSessionManager(
            session_id=session_id, storage_dir=str(STORAGE_DIR)
        ),
        callback_handler=None,
    )

    print("Type 'exit' or Ctrl-D to quit. Your conversation is saved to disk.\n")
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
        print(f"Bot: {agent(user_input)}\n")

    print(f'Goodbye! Session "{session_id}" saved — restart to resume.')


if __name__ == "__main__":
    main()
