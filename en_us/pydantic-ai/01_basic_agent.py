"""
01_basic_agent.py — Simplest possible Pydantic AI Agent

The Pydantic AI equivalent of harness-sdk/01_basic_agent.py.

Demonstrates:
  - Creating an agent in a few lines
  - Using instructions (Pydantic AI's term for the system prompt) to shape behavior
  - Running the agent and getting a response
  - Reading token usage from the run result

Like Strands, Pydantic AI runs the full agent loop:
  Input → Reasoning (LLM) → Tool Selection → Tool Execution → Response

ENVIRONMENT NOTES / LIMITATIONS
-------------------------------
Per .kiro/steering/Permissions.md this environment only permits
`bedrock-runtime:Converse` on `amazon.nova-lite-v1:0` in us-east-1. Pydantic AI
is model-agnostic, so we point it at Amazon Bedrock with Nova Lite via the
BedrockConverseModel provider (the Converse API — same permission Strands uses).

Requires: pip install "pydantic-ai-slim[bedrock]"
"""

from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

# --- Configure the model: Amazon Bedrock + Nova Lite in us-east-1 ---
model = BedrockConverseModel(
    "amazon.nova-lite-v1:0",
    provider=BedrockProvider(region_name="us-east-1"),
)

# --- The simplest agent: model + instructions ---
agent = Agent(
    model,
    instructions="You are a helpful assistant. Be concise.",
)

# Run the agent (synchronously) and get a typed result
result = agent.run_sync("What are the three laws of robotics?")
print("=== Basic Agent Response ===")
print(result.output)

# --- Accessing usage/metrics ---
usage = result.usage
print("\n=== Agent Usage ===")
print(f"Total tokens used: {usage.total_tokens}")
print(f"Input tokens: {usage.input_tokens}")
print(f"Output tokens: {usage.output_tokens}")
print(f"Model requests: {usage.requests}")
