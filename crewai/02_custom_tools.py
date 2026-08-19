"""
02_custom_tools.py — Custom Tools with the @tool Decorator

Demonstrates:
  - Creating tools from plain Python functions (CrewAI's @tool decorator)
  - The agent autonomously choosing which tool(s) to use
  - Direct tool invocation bypassing the agent

Differences from Strands worth knowing:
  - Strands ships built-in `calculator` and `shell` tools in
    strands-agents-tools. CrewAI's extras package (crewai-tools) focuses on
    RAG/search/scraping tools and has no simple calculator or shell tool —
    so here we define both ourselves. With the @tool decorator that is only
    a few lines each, and it shows that "built-in vs custom" is a packaging
    detail, not a capability difference.
  - Strands runs multiple questions against one Agent by calling it
    repeatedly. In CrewAI each question is a Task; a Crew runs the task list
    sequentially with a single agent.
  - CrewAI has no consent prompt around shell execution (Strands'
    BYPASS_TOOL_CONSENT) — the tool runs whatever the model asks. That is why
    the shell tool below is deliberately minimal. Treat it as demo-only.
"""

import os
# Opt out of CrewAI telemetry/tracing before importing crewai (see 01_basic_agent.py).
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

import subprocess

from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from ddgs import DDGS


# --- Custom tool: just a decorated Python function ---
# Like Strands, CrewAI inspects the signature, type hints, and docstring to
# generate the tool schema for the model. The decorator takes the tool name
# as its argument.
@tool("unit_converter")
def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between common units of measurement.

    Args:
        value: The numeric value to convert.
        from_unit: Source unit (e.g., 'km', 'miles', 'kg', 'lbs', 'celsius', 'fahrenheit').
        to_unit: Target unit.

    Returns:
        A string with the conversion result.
    """
    conversions = {
        ("km", "miles"): lambda v: v * 0.621371,
        ("miles", "km"): lambda v: v * 1.60934,
        ("kg", "lbs"): lambda v: v * 2.20462,
        ("lbs", "kg"): lambda v: v * 0.453592,
        ("celsius", "fahrenheit"): lambda v: v * 9 / 5 + 32,
        ("fahrenheit", "celsius"): lambda v: (v - 32) * 5 / 9,
    }

    key = (from_unit.lower(), to_unit.lower())
    if key not in conversions:
        return f"Cannot convert from {from_unit} to {to_unit}"

    result = conversions[key](value)
    return f"{value} {from_unit} = {result:.2f} {to_unit}"


# --- Another custom tool ---
@tool("word_stats")
def word_stats(text: str) -> str:
    """Analyze text and return word statistics.

    Args:
        text: The text to analyze.

    Returns:
        Statistics about the text including word count, character count, etc.
    """
    words = text.split()
    return (
        f"Words: {len(words)}, "
        f"Characters: {len(text)}, "
        f"Sentences: {text.count('.') + text.count('!') + text.count('?')}, "
        f"Average word length: {sum(len(w) for w in words) / len(words):.1f}"
    )


# --- Calculator (built-in in Strands; custom here) ---
@tool("calculator")
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A Python-style arithmetic expression, e.g. '100 * 0.621371'.

    Returns:
        The numeric result as a string.
    """
    try:
        # Demo-only: eval with no builtins. Use a real math parser in production.
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculation error: {e}"


# --- Shell (built-in in Strands; custom here) ---
@tool("shell")
def shell(command: str) -> str:
    """Run a shell command and return its output.

    Args:
        command: The shell command to execute, e.g. 'date' or 'pwd'.

    Returns:
        The command's stdout (and stderr on failure).
    """
    # Demo-only: no confirmation step. Never expose unrestricted shell
    # execution to a model in production.
    proc = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=30
    )
    output = proc.stdout.strip()
    if proc.returncode != 0:
        output += f"\n[exit code {proc.returncode}] {proc.stderr.strip()}"
    return output or "(no output)"


# --- Web search tool using DuckDuckGo (ddgs) ---
@tool("web_search")
def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using DuckDuckGo and return results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default: 3).

    Returns:
        Search results with titles, URLs, and snippets.
    """
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        output = []
        for r in results:
            output.append(f"• {r['title']}\n  {r['href']}\n  {r['body']}")
        return "\n\n".join(output)
    except Exception as e:
        return f"Search error: {e}"


# --- Create agent with multiple tools ---
llm = LLM(model="bedrock/amazon.nova-lite-v1:0")

agent = Agent(
    role="Multi-Tool Assistant",
    goal="Answer questions using the most appropriate tool for each job.",
    backstory=(
        "You are a helpful assistant with access to a calculator, unit converter, "
        "word statistics tool, web search, and a shell tool for running system commands."
    ),
    tools=[calculator, unit_converter, word_stats, web_search, shell],
    llm=llm,
    verbose=False,
)

# --- Each question becomes a Task; the agent decides which tool(s) to use ---
questions = [
    ("Convert 100 km to miles and verify",
     "Convert 100 kilometers to miles, then calculate 100 * 0.621371 to verify."),
    ("Word stats",
     "How many words are in: 'The quick brown fox jumps over the lazy dog'?"),
    ("Web search for CrewAI",
     "Search the web for 'CrewAI framework' and summarize what it is."),
    ("Shell - date and working directory",
     "Use the shell tool to show the current date and the current working directory."),
]

print("=== Agent Chooses Tools Autonomously ===\n")
for label, question in questions:
    task = Task(
        description=question,
        expected_output="A concise answer based on the tool results.",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    print(f"Q: {label}\nA: {result}\n")

# --- Direct tool invocation (bypasses agent reasoning) ---
# In Strands: agent.tool.unit_converter(...). In CrewAI, call the Tool
# object's .run() method directly.
print("=== Direct Tool Invocation ===\n")
result = unit_converter.run(value=72, from_unit="fahrenheit", to_unit="celsius")
print(f"Direct call: 72°F → Celsius = {result}")
