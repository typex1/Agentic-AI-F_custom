# 06 — Session Management

**Python file:** [`../06_session_management.py`](../06_session_management.py)

## Learning objective
Persist an agent's conversation so it can be resumed later, retaining memory of
prior turns across separate runs.

## Why it matters
By default an agent starts every conversation from scratch. Production agents
(chatbots, assistants, long-running workflows) need durable state across
invocations, restarts, and processes.

## What this example demonstrates
- Attaching a `FileSessionManager` to persist a conversation to disk.
- Resuming the same session in a fresh agent instance using its `session_id`.
- Verifying the resumed agent recalls facts established in the earlier session.

## Key concepts
`FileSessionManager`, `session_id`, conversation persistence and resumption
(other backends: S3, custom).
