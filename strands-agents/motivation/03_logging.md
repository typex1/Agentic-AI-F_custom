# Observing Tool Use Through Logging

**Python file:** [`../03_logging.py`](../03_logging.py)

## Learning objective
Make the agent loop visible: watch which tool the model picks, the arguments
it passes, the result that comes back, and the full prompt/context sent to the
model on every turn.

## Why it matters
Tool use looks like magic until you see the mechanics. Logging reveals that it
is just structured data flowing through the context: a tool catalog teaches the
model what it can call, the model replies with a `toolUse` request, the SDK
runs your Python function, and the `toolResult` is fed back in. Understanding
this flow is the foundation for debugging agents — and for later modules on
guardrails and prompt injection, where "what exactly went into the context?"
becomes a security question.

## What this example demonstrates
- A deliberately small setup — two tools only, so the logs stay readable:
  the built-in `current_time` (from `strands_tools`) and the custom
  `unit_converter` (`@tool` decorator).
- Configuring logging per the official Strands approach: the `strands` logger
  hierarchy, a structured pipe-delimited format, and a custom `FileHandler`
  writing to `logs/03_logging.log` (truncated on every run).
- A *focused* view by default: the framework stays at WARNING while our own
  hooks log the interesting lines; `FULL_TRACE = True` switches to the
  complete framework DEBUG firehose.
- Logging tool calls via the **public hooks API** instead of SDK-internal
  logger names — upgrade-stable by design:
  - `ToolUseLogger` on `BeforeToolCallEvent`/`AfterToolCallEvent` emits one
    `TOOL CALL` line (tool name + arguments) and one `TOOL RESULT` line
    (status) per invocation.
  - `PromptContextLogger` on `BeforeModelCallEvent` logs the tool catalog once
    and the growing message history (with `toolUse`/`toolResult` entries)
    before every model call.
- Direct tool invocation (`agent.tool.unit_converter(...)`) is captured by the
  same hooks, even though it bypasses the model.

## Key concepts
The `strands` logger hierarchy, `logging.basicConfig` + `FileHandler`,
`HookProvider`/`HookRegistry`, `BeforeModelCallEvent`,
`BeforeToolCallEvent`/`AfterToolCallEvent`, tool catalog (tool specs) in the
request context, `toolUse`/`toolResult` message blocks, `callback_handler=None`.
