# Task 1 — Reference Solution: Kiro-Replica CLI

A well-implemented reference for [`../../tasks/1-kiro-replica.md`](../../tasks/1-kiro-replica.md).
Compare your own solution against this *after* you have attempted the task.

## Files

| File | Role |
|------|------|
| `kiro-replica-cli.sh` | Thin launcher — resolves its own directory and runs the Python program. |
| `kiro_replica.py`     | The agent (Nova Lite + `shell` + `web_search`) and the interactive REPL. |

## Run

```bash
cd strands-agents/solutions/1-kiro-replica
./kiro-replica-cli.sh          # asks before running each shell command (safe default)
./kiro-replica-cli.sh --yolo   # runs shell commands without confirmation (unattended)
```

Then try, for example:

```
kiro> What files are in this directory and which is largest?   # -> shell tool
kiro> What is the latest stable Python version?                # -> web_search tool
kiro> Remind me what I just asked you.                         # -> uses session history
```

Type `/help` for commands, `exit` / `quit` / Ctrl-D to leave.

## How it meets the requirements

- **Nova Lite only** — the `Agent` is bound to `amazon.nova-lite-v1:0`; no other
  provider is configured.
- **Shell** — uses the `shell` tool from `strands_tools`.
- **Web search** — a custom `@tool` built on DuckDuckGo (`ddgs`), reused from
  demo `02_custom_tools.py`.
- **Interactive session** — a `while True:` REPL that reuses a single `Agent`
  instance, so conversation history persists for the whole session.
- **Streaming UX** — a `callback_handler` prints tokens live and shows a
  `🔧 [tool]` indicator when a tool fires.

## Design choices worth noting

- **Safety first for shell access.** By default the `shell` tool prompts for
  confirmation before executing anything. `--yolo` sets
  `BYPASS_TOOL_CONSENT=true` to skip that — convenient for demos, risky in
  general. Letting a human approve commands is a deliberate, safer design.
- **The model, not the code, chooses the tool.** There is no `if "search" in
  input` routing. Nova Lite decides when to shell out vs. search, based on the
  system prompt and the tool descriptions. That is the essence of an agent.
- **Resilient loop.** Tool/model errors are caught per turn so a single failure
  does not end the session.

## Prerequisites

- `pip install -r ../../../requirements.txt` (or at least `strands-agents`,
  `strands-agents-tools`, `ddgs`).
- AWS credentials with `bedrock-runtime` access to Nova Lite in `us-east-1`.
