# Task 1 — Build a Minimal Kiro-CLI Replica

## Goal

Build a small, interactive command-line coding assistant — a stripped-down
replica of Kiro CLI — using the **Strands Agents SDK**.

You are experienced developers, but likely new to agentic AI frameworks. The
point of this task is *not* to ship a polished product. It is to get hands-on
with the core agentic loop: an LLM that reasons, decides to call **tools**, acts
on the results, and keeps going until it can answer you.

Keep it simple. We will extend it in later tasks.

## What you build

A shell entrypoint, `kiro-replica-cli.sh`, that launches an interactive terminal
session with an agent. The agent must be:

1. **Backed by Amazon Nova Lite** (`amazon.nova-lite-v1:0`) on Amazon Bedrock.
   This is the *only* model we have access to in this environment (see the
   permissions note below) — do not wire up OpenAI, Anthropic, Ollama, etc.
2. **Able to run shell commands** on the local machine.
3. **Able to perform an internet search.**

That is the entire required feature set. No file-editing tools, no MCP, no
multi-agent orchestration, no sessions — those come later.

## Functional requirements

- `./kiro-replica-cli.sh` starts a **REPL-style loop**: it prints a prompt,
  reads a line of user input, sends it to the agent, prints the agent's
  response, and repeats.
- The user can type something like `exit` or `quit` (or press Ctrl-D) to leave
  the session cleanly.
- Conversation context is preserved across turns within a single session (the
  agent should remember what you said two messages ago).
- When the agent decides to run a shell command or search the web, that should
  actually happen and the result should feed back into its answer. For example:
  - *"What files are in this directory and how big is the largest one?"* → the
    agent uses the shell tool.
  - *"What's the latest stable version of Python?"* → the agent uses web search.
- The shell script should launch the Python program (e.g. `python kiro_replica.py`).
  Put the agent logic in a `.py` file; keep the `.sh` file thin.

## Suggested structure

```
tasks/
  solution/                  # your work goes here (create this)
    kiro-replica-cli.sh      # thin launcher
    kiro_replica.py          # the agent + REPL loop
```

## Building blocks you already have

Everything you need has an example in `strands-agents/`. Study these first:

| Example | What to borrow from it |
|---------|------------------------|
| `01_basic_agent.py`  | Creating an `Agent` bound to `amazon.nova-lite-v1:0` and a system prompt. |
| `02_custom_tools.py` | The `shell` tool from `strands_tools`, and a `web_search` tool built on `ddgs` (DuckDuckGo). Copy the `web_search` pattern. |

The `@tool` decorator turns any Python function into something the agent can
call. The SDK runs the whole loop (reason → pick tool → execute → continue) for
you.

## Hints

- The interactive loop is just a `while True:` around `input(...)` that calls
  `agent(user_text)`. The `Agent` object holds the conversation history, so
  reuse the *same* agent instance across turns.
- `strands_tools`' `shell` tool prompts for confirmation before running a
  command. For an unattended demo you can set
  `os.environ["BYPASS_TOOL_CONSENT"] = "true"` — but think about *why* a real
  coding assistant asks before running commands. Making the human approve each
  command is a legitimate (and safer) design choice.
- For web search, reuse the `web_search` tool from `02_custom_tools.py`
  (`from ddgs import DDGS`).
- Streaming with a `callback_handler` (see the Strands docs on callback
  handlers) gives a much
  nicer UX than waiting for the full response. Show tool calls as they happen.
- Make `kiro-replica-cli.sh` executable: `chmod +x kiro-replica-cli.sh`.

## Permissions / environment note

This environment only allows **`bedrock-runtime`** actions (`Converse`,
`ConverseStream`, `InvokeModel`, `InvokeModelWithResponseStream`) on **Nova
Lite** in **`us-east-1`**. There is no Bedrock control-plane access and no other
model. Strands works here because it only uses `Converse` / `ConverseStream`.
See `.kiro/steering/Permissions.md` and `Model_permissions.md` for details.

Make sure dependencies are installed (`ddgs`, `strands-agents`,
`strands-agents-tools`) — see the top-level `README.md` and `requirements.txt`.

## Acceptance criteria

- [ ] `./kiro-replica-cli.sh` starts an interactive session and exits cleanly.
- [ ] The agent uses **only** Nova Lite (`amazon.nova-lite-v1:0`).
- [ ] Asking a question that needs the local system triggers a **shell command**
      and the answer reflects the real output.
- [ ] Asking a question about current/external information triggers a
      **web search** and the answer reflects the results.
- [ ] The agent remembers earlier turns within the same session.

## Stretch goals (optional)

- Stream tokens live and print a small indicator (e.g. `🔧 [shell]`) when a tool
  fires.
- Require human confirmation before executing any shell command.
- Add a `/help` command and a startup banner.
- Gracefully handle tool errors (e.g. a failed search) without crashing the loop.

## Reflection questions

Jot down brief answers — we will discuss these:

1. Who decides *whether* to run a shell command vs. search the web — your code,
   or the model? What does that tell you about how agents differ from ordinary
   scripts?
2. What are the risks of giving an LLM shell access, and how would you mitigate
   them?
3. Where does the conversation history live, and what happens as it grows?
