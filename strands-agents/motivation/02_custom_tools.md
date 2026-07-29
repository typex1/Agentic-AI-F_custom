# Custom Tools

**Python file:** [`../02_custom_tools.py`](../02_custom_tools.py)

## Learning objective
Extend an agent beyond conversation by giving it tools, and see the agent
autonomously decide which tool(s) to use for a given request.

## Why it matters
Tools are what turn a chatbot into an agent. This shows how little code it takes
to expose real capabilities and how the model routes to them on its own.

## What this example demonstrates
- Turning plain Python functions into tools with the `@tool` decorator
  (`unit_converter`, `word_stats`, `web_search`).
- Combining custom tools with built-in ones from `strands_tools`
  (`calculator`, `shell`).
- A real web-search tool backed by DuckDuckGo (`ddgs`).
- Autonomous, multi-tool selection by the model, plus **direct tool invocation**
  (`agent.tool.<name>(...)`) that bypasses the model.

## Key concepts
`@tool`, tool schemas from type hints + docstrings, built-in tools, direct tool
invocation, the sandboxed `shell` tool (and `BYPASS_TOOL_CONSENT`).
