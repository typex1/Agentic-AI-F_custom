"""
03_logging.py — Observing Tool Use Through Logging

Same tools as 02_custom_tools.py, but with logging turned on so you can *watch*
the agent's tool-use decisions instead of just seeing the final answer.

Goal of this demo:
  - Enable the framework's own logging (the `strands` logger)
  - Watch each step of the agent loop: which tool the model picks, the
    arguments it passes, and the result that comes back
  - See the *actual prompt/context* sent to the model on every turn, to make a
    key point clear: tool use adds a lot of extra content to the context —
      * a "tools available" catalog (each tool's name, description and
        parameter schema) so the model knows what it can call, and
      * the growing conversation, where the model's chosen tool + populated
        parameters (`toolUse`) and each tool's output (`toolResult`) are fed
        back in so the model can reason over them.
  - Understand that "tool use" is just the model emitting a structured
    tool-call request, the SDK executing your Python function, and feeding the
    result back into the conversation

The logging setup below mirrors the approach introduced in Lab-2/Task.py
(Task 2.4 "Configure logging"), but writes to a file
(strands-agents/logs/03_logging.log) instead of the console. The file is
truncated on every run so it only ever holds the most recent execution. By
default it captures a *focused* view — just the per-tool invocation line from
the tool executor — while keeping the rest of the framework quiet.
`callback_handler=None` keeps the streamed model tokens out of the way so the
log stays clean.

Inspect the tool use with, e.g.:
    tail -f strands-agents/logs/03_logging.log

Tip: set `FULL_TRACE = True` below to capture the entire agent-loop firehose
(model requests/responses, retries, tool registry) — verbose but complete.

NOTE: The `shell` tool executes real system commands. It normally prompts
for confirmation; this demo sets BYPASS_TOOL_CONSENT=true to run unattended.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import os
# The strands_tools `shell` tool asks for confirmation before running commands.
# For this non-interactive demo we bypass that prompt. Remove this line in
# production or when you want a human to approve each command.
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# --- Logging: this is what makes tool use observable --------------------------
# Modeled on Lab-2/Task.py (Task 2.4). basicConfig installs a console handler
# and a readable format.
#
# The teaching goal here is to SEE tool use. If you simply set the whole
# `strands` logger to DEBUG you technically get that — but you also get the full
# request payload (every tool's JSON schema) re-printed on every turn, which
# buries the interesting lines. So instead we take a *focused* approach:
#
#   - keep the framework generally quiet (WARNING), then
#   - turn DEBUG on for ONLY the tool executor, whose log line reads:
#       strands.tools.executors._executor | tool_use=<{'name': ..., 'input': ...}>
#     i.e. exactly the tool the model picked and the arguments it passed.
#
# Flip FULL_TRACE to True to see the entire agent-loop firehose (model
# requests/responses, retries, tool registry, etc.) — verbose but complete.
import logging
from pathlib import Path

FULL_TRACE = False

# Write logs to a file next to this script (strands-agents/logs/03_logging.log),
# not to stdout. Resolve the path relative to THIS file so it works no matter
# what the current working directory is.
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "03_logging.log"

# Remove any log from a previous run so the file doesn't grow without bound.
LOG_FILE.unlink(missing_ok=True)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    # mode="w" also starts fresh; combined with the unlink above the log always
    # reflects just the most recent run.
    handlers=[logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")],
)

if FULL_TRACE:
    # Everything the framework logs — great for deep debugging, noisy for demos.
    logging.getLogger("strands").setLevel(logging.DEBUG)
else:
    # Focused view: quiet framework, but show each tool invocation.
    logging.getLogger("strands").setLevel(logging.WARNING)
    logging.getLogger("strands.tools.executors").setLevel(logging.DEBUG)

# Keep noisy third-party loggers quiet so the agent's tool use stands out.
for noisy in ("botocore", "boto3", "urllib3", "httpx", "httpcore", "primp"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

# A logger of our own, so our narration lines look like the framework's.
logger = logging.getLogger("tool_use_demo")
logger.setLevel(logging.INFO)

# A dedicated logger for the prompt/context we send to the model. We keep it at
# DEBUG (always, regardless of FULL_TRACE) because seeing the prompt is the
# whole point of this file — and it lands in the same log file.
prompt_logger = logging.getLogger("prompt_context")
prompt_logger.setLevel(logging.DEBUG)

from strands import Agent, tool
# The `calculator` and `shell` tools ship with `strands-agents-tools`. To see
# exactly how a production-grade tool is written (the @tool decorator, the
# docstring/type-hint schema, argument handling and error reporting), read the
# original source on GitHub:
#   calculator: https://github.com/strands-agents/tools/blob/main/src/strands_tools/calculator.py
#   (browse the folder for shell.py and the other built-in tools)
#     https://github.com/strands-agents/tools/tree/main/src/strands_tools
from strands_tools import calculator, shell
from ddgs import DDGS

import json
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeModelCallEvent


# --- Hook: log the prompt/context sent to the model ---------------------------
# A HookProvider lets us tap into the agent loop. We register a callback on
# BeforeModelCallEvent, which fires right before every model inference — the
# exact moment the full prompt (system prompt + tool catalog + running message
# history) is about to be sent. Logging it here makes visible that tool use is
# powered by extra content injected into the context.
class PromptContextLogger(HookProvider):
    """Logs, to the log file, everything that is sent to the model each turn."""

    def __init__(self, log: logging.Logger):
        self._log = log
        self._tools_logged = False

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeModelCallEvent, self._on_before_model_call)

    def _on_before_model_call(self, event: BeforeModelCallEvent) -> None:
        agent = event.agent

        # (1) The "tools available" catalog. This is identical on every turn, so
        # we log it once — it's the extended content that teaches the model
        # which tools exist and what parameters each one accepts.
        if not self._tools_logged:
            specs = agent.tool_registry.get_all_tool_specs()
            self._log.debug(
                "TOOL CATALOG injected into every request "
                "(%d tools: %s):\n%s",
                len(specs),
                ", ".join(agent.tool_names),
                json.dumps(specs, indent=2, default=str),
            )
            self._tools_logged = True

        # (2) The prompt actually sent this turn: the system prompt plus the
        # running message history. As the loop progresses you'll see it grow
        # with the model's `toolUse` picks (name + populated parameters) and the
        # `toolResult` entries fed back in.
        self._log.debug(
            "PROMPT SENT TO MODEL — system prompt + %d message(s):\n%s",
            len(agent.messages),
            json.dumps(
                {"system_prompt": agent.system_prompt, "messages": agent.messages},
                indent=2,
                default=str,
            ),
        )


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
    tools=[calculator, unit_converter, word_stats, web_search, shell],
    system_prompt=(
        "You are a helpful assistant with access to a calculator, unit converter, "
        "word statistics tool, web search, and a shell tool for running system commands."
    ),
    callback_handler=None,
    # This hook logs the full prompt/context (tool catalog + messages) sent to
    # the model on every turn — see PromptContextLogger above.
    hooks=[PromptContextLogger(prompt_logger)],
)

# The agent decides which tool(s) to use based on the question
print("=== Agent Chooses Tools Autonomously ===\n")
print(f"(tool-use logs are being written to: {LOG_FILE})\n")
logger.info("Each 'strands.tools.executors._executor' line below shows the tool "
            "the model selected and the arguments it passed.")

response = agent("Convert 100 kilometers to miles, then calculate 100 * 0.621371 to verify.")
print(f"Q: Convert 100 km to miles and verify\nA: {response}\n")

response = agent("How many words are in: 'The quick brown fox jumps over the lazy dog'?")
print(f"Q: Word stats\nA: {response}\n")

response = agent("Search the web for 'Strands Agents SDK' and summarize what it is.")
print(f"Q: Web search for Strands Agents SDK\nA: {response}\n")

response = agent("Use the shell tool to show the current date and the current working directory.")
print(f"Q: Shell - date and working directory\nA: {response}\n")

# --- Direct tool invocation (bypasses agent reasoning) ---
print("=== Direct Tool Invocation ===\n")
result = agent.tool.unit_converter(value=72, from_unit="fahrenheit", to_unit="celsius")
print(f"Direct call: 72°F → Celsius = {result}")
