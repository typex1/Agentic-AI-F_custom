"""
12_session_management.py — Conversation Persistence

Demonstrates:
  - Saving agent conversations to disk
  - Resuming conversations from a previous session
  - The agent remembering prior context after reload

The Strands SDK provides session managers (file-based, S3, or custom)
so your agents can maintain state across invocations.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import os
import uuid
import tempfile
import shutil
from strands import Agent
from strands.session import FileSessionManager


# --- Set up a temporary directory for session storage ---
session_dir = tempfile.mkdtemp(prefix="strands_sessions_")
session_id = str(uuid.uuid4())
print(f"Session storage: {session_dir}")
print(f"Session ID: {session_id}\n")

# --- First conversation: establish context ---
print("=== Session 1: Establishing Context ===\n")

session_manager = FileSessionManager(session_id=session_id, storage_dir=session_dir)

agent = Agent(
    model="amazon.nova-lite-v1:0",
    system_prompt="You are a helpful assistant. Remember details the user tells you.",
    callback_handler=None,
    session_manager=session_manager,
)

response = agent("My name is Alex and I'm working on a project called Neptune.")
print(f"User: My name is Alex and I'm working on a project called Neptune.")
print(f"Agent: {response}\n")

response = agent("The project is about building an underwater drone for ocean research.")
print(f"User: The project is about building an underwater drone for ocean research.")
print(f"Agent: {response}\n")

print(f"[Session saved: {session_id}]")

# --- Simulate closing and reopening (new agent instance) ---
print("\n=== Session 2: Resuming Previous Conversation ===\n")

# Create a fresh session manager pointing to the same session
resumed_session_manager = FileSessionManager(session_id=session_id, storage_dir=session_dir)

resumed_agent = Agent(
    model="amazon.nova-lite-v1:0",
    system_prompt="You are a helpful assistant. Remember details the user tells you.",
    callback_handler=None,
    session_manager=resumed_session_manager,
)

# The agent should remember the context from Session 1
response = resumed_agent("What's my name and what project am I working on?")
print(f"User: What's my name and what project am I working on?")
print(f"Agent: {response}\n")

response = resumed_agent("What kind of device is the project building?")
print(f"User: What kind of device is the project building?")
print(f"Agent: {response}")

# --- Cleanup ---
shutil.rmtree(session_dir)
print(f"\n[Cleaned up session storage]")
