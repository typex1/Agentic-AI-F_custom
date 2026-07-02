"""
05_multi_agent.py — Agents as Tools (Multi-Agent Pattern)

Demonstrates:
  - Creating specialized agents for different tasks
  - Using one agent as a tool for another (agents-as-tools pattern)
  - An orchestrator agent delegating to specialist agents

This is the simplest multi-agent pattern: the orchestrator decides which
specialist to call based on the user's request.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent, tool


# --- Specialist Agent 1: Code Reviewer ---
code_reviewer = Agent(
    model="amazon.nova-lite-v1:0",
    system_prompt="""You are an expert code reviewer. When given code, provide:
    1. A brief quality assessment (good/needs work/poor)
    2. Key issues found (if any)
    3. One improvement suggestion
    Keep your response to 3-4 sentences max.""",
    callback_handler=None,
)


# --- Specialist Agent 2: Explainer ---
explainer = Agent(
    model="amazon.nova-lite-v1:0",
    system_prompt="""You are a code explainer for beginners. When given code, explain
    what it does in simple, plain language. Use analogies where helpful.
    Keep your response to 2-3 sentences.""",
    callback_handler=None,
)


# --- Wrap specialists as tools for the orchestrator ---
@tool
def review_code(code: str) -> str:
    """Review code for quality, bugs, and best practices.

    Args:
        code: The code snippet to review.

    Returns:
        A code review with quality assessment and suggestions.
    """
    response = code_reviewer(f"Review this code:\n```\n{code}\n```")
    return str(response)


@tool
def explain_code(code: str) -> str:
    """Explain code in simple terms for beginners.

    Args:
        code: The code snippet to explain.

    Returns:
        A beginner-friendly explanation of what the code does.
    """
    response = explainer(f"Explain this code:\n```\n{code}\n```")
    return str(response)


# --- Orchestrator agent that delegates to specialists ---
orchestrator = Agent(
    model="amazon.nova-lite-v1:0",
    tools=[review_code, explain_code],
    system_prompt="""You are a coding assistant orchestrator. Based on the user's request:
    - If they want a code review, use the review_code tool
    - If they want an explanation, use the explain_code tool
    - If they want both, use both tools
    Summarize the results concisely.""",
    callback_handler=None,
)

# --- Demo ---
sample_code = """
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
"""

print("=== Multi-Agent: Agents as Tools ===\n")
print(f"Code under analysis:\n{sample_code}")

print("--- Request: Explain the code ---")
response = orchestrator(f"Explain this code for a beginner:\n{sample_code}")
print(f"\n{response}\n")

print("--- Request: Review the code ---")
response = orchestrator(f"Review this code for quality:\n{sample_code}")
print(f"\n{response}")
