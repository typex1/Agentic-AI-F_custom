# 04 — Streaming & Callback Handlers

**Python file:** [`../11_streaming.py`](../11_streaming.py)

## Learning objective
React to an agent's output and actions in real time, as they happen, rather than
waiting for the final response.

## Why it matters
Responsive UIs, live logging, and progress indicators all depend on streaming.
Callback handlers are also the hook point for observing tool use as it occurs.

## What this example demonstrates
- A custom `callback_handler` that receives streaming events.
- Printing text chunks token-by-token as they are generated.
- Detecting and reporting tool-use events in real time.
- Tracking which tools were invoked across multiple queries.

## Key concepts
`callback_handler`, streaming events (`data`, `current_tool_use`), real-time
event processing, agent lifecycle visibility.
