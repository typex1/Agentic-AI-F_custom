# 12 — Conversation Management

**Python file:** [`../14_conversation_management.py`](../14_conversation_management.py)

## Learning objective
Control how an agent's message history grows so it stays within the model's
context window, using the three built-in strategies.

## Why it matters
Long or tool-heavy conversations eventually overflow the context window.
Choosing the right management strategy is a core production concern that affects
cost, latency, and how much the agent "remembers."

## What this example demonstrates
- `SlidingWindowConversationManager` — keep only the last N messages (preserving
  tool-use/result pairs).
- `NullConversationManager` — keep everything; raise on overflow (you manage it).
- `SummarizingConversationManager` — summarize old turns instead of dropping
  them, preserving the gist (verified recall of earlier facts).

## Key concepts
`SlidingWindowConversationManager`, `NullConversationManager`,
`SummarizingConversationManager`, `window_size`, `summary_ratio`,
`preserve_recent_messages`, context-window limits.
