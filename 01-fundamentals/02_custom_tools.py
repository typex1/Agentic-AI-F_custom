"""
02_custom_tools.py — Custom Tools with @tool Decorator

Demonstrates:
  - Creating tools from plain Python functions
  - The agent autonomously choosing which tool(s) to use
  - Combining built-in tools (calculator, bash) with custom tools
  - Direct tool invocation bypassing the agent

The @tool decorator inspects your function's signature, docstring, and type
hints to generate the tool schema the model needs — zero boilerplate.

NOTE: The `bash` tool (vended by strands-agents; replaces the deprecated
`shell` tool removed in strands-agents-tools v0.9.0) executes real system
commands and runs WITHOUT a confirmation prompt.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent, tool
from strands.vended_tools import bash
from strands_tools import calculator
from ddgs import DDGS


# --- Custom tool: just a decorated Python function ---
@tool
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
@tool
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


# --- Web search tool using DuckDuckGo (ddgs) ---
@tool
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
agent = Agent(
    model="amazon.nova-lite-v1:0",
    tools=[calculator, unit_converter, word_stats, web_search, bash],
    system_prompt=(
        "You are a helpful assistant with access to a calculator, unit converter, "
        "word statistics tool, web search, and a bash tool for running system commands."
    ),
    callback_handler=None,
)

# The agent decides which tool(s) to use based on the question
print("=== Agent Chooses Tools Autonomously ===\n")

response = agent("Convert 100 kilometers to miles, then calculate 100 * 0.621371 to verify.")
print(f"Q: Convert 100 km to miles and verify\nA: {response}\n")

response = agent("How many words are in: 'The quick brown fox jumps over the lazy dog'?")
print(f"Q: Word stats\nA: {response}\n")

response = agent("Search the web for 'Strands Agents SDK' and summarize what it is.")
print(f"Q: Web search for Strands Agents SDK\nA: {response}\n")

response = agent("Use the bash tool to show the current date and the current working directory.")
print(f"Q: Shell - date and working directory\nA: {response}\n")

# --- Direct tool invocation (bypasses agent reasoning) ---
print("=== Direct Tool Invocation ===\n")
result = agent.tool.unit_converter(value=72, from_unit="fahrenheit", to_unit="celsius")
print(f"Direct call: 72°F → Celsius = {result}")
