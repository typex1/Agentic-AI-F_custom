"""
01_basic_agent.py — Simplest possible CrewAI agent

Demonstrates:
  - Creating an agent with a role, goal, and backstory (CrewAI's "persona" model)
  - Pairing it with a Task and running it via a Crew
  - Calling the crew and getting a response

CrewAI's mental model differs from Strands:
  - Strands: ONE Agent object you call like a function.
  - CrewAI:  Agents have a persona (role/goal/backstory) and work on explicit
             Task objects; a Crew orchestrates agents + tasks.
             Crew.kickoff() runs the loop:
             Task → Reasoning (LLM) → Tool Selection → Tool Execution → Response
"""

import os
# CrewAI phones home (telemetry + optional tracing) via OpenTelemetry by
# default. On boxes without outbound access to their collector this adds a
# ~30-60s export timeout at exit — so we opt out before importing crewai.
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

# --- The model: Amazon Nova Lite via Bedrock ---
# CrewAI uses LiteLLM under the hood, so Bedrock models are addressed with a
# "bedrock/" prefix (credentials/region come from the usual AWS env/config).
llm = LLM(model="bedrock/amazon.nova-lite-v1:0")

# --- The simplest agent ---
# Instead of a single system prompt, CrewAI builds the system prompt from
# role + goal + backstory.
agent = Agent(
    role="Helpful Assistant",
    goal="Answer questions accurately and concisely.",
    backstory="You are a helpful assistant. Be concise.",
    llm=llm,
    verbose=False,  # Suppress step-by-step console output; we print the final result
)

# --- The task: what the agent should do ---
task = Task(
    description="What are the three laws of robotics?",
    expected_output="A concise listing of the three laws of robotics.",
    agent=agent,
)

# --- The crew: binds agents and tasks together and runs them ---
crew = Crew(agents=[agent], tasks=[task], verbose=False)

result = crew.kickoff()
print("=== Basic Agent Response ===")
print(result)

# --- Accessing metrics ---
usage = result.token_usage
print("\n=== Agent Metrics ===")
print(f"Total tokens used: {usage.total_tokens}")
print(f"Prompt tokens: {usage.prompt_tokens}")
print(f"Completion tokens: {usage.completion_tokens}")
print(f"Successful LLM requests: {usage.successful_requests}")
