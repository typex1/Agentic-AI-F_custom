"""
11_streaming.py — Streaming and Callback Handlers

Demonstrates:
  - Custom callback handlers for real-time token streaming
  - Tracking tool usage events as they happen
  - Understanding the agent lifecycle events

The Strands SDK streams tokens as they're generated, letting you build
responsive UIs, logging pipelines, or real-time displays.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent, tool
from strands_tools import calculator


# --- Custom callback handler ---
tool_calls_seen = []


def my_callback_handler(**kwargs):
    """A callback handler that processes streaming events in real-time."""

    if "data" in kwargs:
        # Text chunks as they're generated (token by token)
        print(kwargs["data"], end="", flush=True)

    elif "current_tool_use" in kwargs:
        # Tool invocation events
        tool_info = kwargs["current_tool_use"]
        tool_id = tool_info.get("toolUseId", "")
        tool_name = tool_info.get("name", "")

        if tool_name and tool_id not in tool_calls_seen:
            tool_calls_seen.append(tool_id)
            print(f"\n  🔧 [Tool: {tool_name}]", flush=True)

    elif "complete" in kwargs:
        # Agent finished responding
        print("\n  ✓ [Complete]", flush=True)


# --- Create a simple tool to demonstrate tool events ---
@tool
def get_fun_fact(topic: str) -> str:
    """Get a fun fact about a topic.

    Args:
        topic: The topic to get a fun fact about.

    Returns:
        A fun fact string.
    """
    facts = {
        "python": "Python was named after Monty Python's Flying Circus, not the snake!",
        "space": "A day on Venus is longer than its year.",
        "math": "111,111,111 × 111,111,111 = 12,345,678,987,654,321",
    }
    return facts.get(topic.lower(), f"Here's a fact: {topic} is fascinating!")


# --- Agent with custom streaming callback ---
agent = Agent(
    model="amazon.nova-lite-v1:0",
    tools=[calculator, get_fun_fact],
    system_prompt="You are a concise, fun assistant. Keep responses brief.",
    callback_handler=my_callback_handler,
)

print("=== Streaming with Callback Handler ===\n")
print("--- Query 1: Uses fun_fact tool ---")
response = agent("Tell me a fun fact about Python the programming language.")

print("\n\n--- Query 2: Uses calculator tool ---")
tool_calls_seen.clear()
response = agent("What is 2^10 * 3?")

print("\n\n=== Summary ===")
print(f"Total tool calls observed: {len(tool_calls_seen)}")
