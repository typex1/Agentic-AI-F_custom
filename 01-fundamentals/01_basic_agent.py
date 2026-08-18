"""
01_basic_agent.py — Simplest possible Strands Agent

Demonstrates:
  - Creating an agent in 3 lines
  - Using a system prompt to shape behavior
  - Calling the agent and getting a response

The Strands SDK handles the entire agent loop:
  Input → Reasoning (LLM) → Tool Selection → Tool Execution → Response
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent

# --- The simplest agent: just 3 lines ---
agent = Agent(
    model="amazon.nova-lite-v1:0",
    system_prompt="You are a helpful assistant. Be concise.",
    callback_handler=None,  # Suppress streaming output; we print the final result
)

# Call the agent like a function
response = agent("What are the three laws of robotics?")
print("=== Basic Agent Response ===")
print(response)

# --- Accessing metrics ---
summary = response.metrics.get_summary()
print("\n=== Agent Metrics ===")
print(f"Total tokens used: {summary['accumulated_usage']['totalTokens']}")
print(f"Latency: {summary['accumulated_metrics']['latencyMs']}ms")
print(f"Agent loop cycles: {summary['total_cycles']}")
