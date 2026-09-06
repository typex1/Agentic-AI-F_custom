"""
03_logging.py — Observing Tool Use Through Logging

A deliberately small setup — just two tools — with logging turned on so you
can *watch* the agent's tool-use decisions instead of just seeing the final
answer:
  - `current_time` (built-in, from strands-agents-tools)
  - `unit_converter` (custom, defined below with the @tool decorator)

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

The logging setup below mirrors the approach introduced in Lab-2_original/Task.py
(Task 2.4 "Configure logging"), but writes to a file
(strands-agents/logs/03_logging.log) instead of the console. The file is
truncated on every run so it only ever holds the most recent execution. By
default it captures a *focused* view — one line per tool call and one per tool
result, emitted by our own hook (see ToolUseLogger below) — while keeping the
framework itself quiet. `callback_handler=None` keeps the streamed model
tokens out of the way so the log stays clean.

Inspect the tool use with, e.g.:
    tail -f strands-agents/logs/03_logging.log

Tip: set `FULL_TRACE = True` below to capture the entire agent-loop firehose
(model requests/responses, retries, tool registry) — verbose but complete.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

# --- Logging: this is what makes tool use observable --------------------------
# Modeled on Lab-2_original/Task.py (Task 2.4). basicConfig installs a console handler
# and a readable format.
#
# The teaching goal here is to SEE tool use. If you simply set the whole
# `strands` logger to DEBUG you technically get that — but you also get the full
# request payload (every tool's JSON schema) re-printed on every turn, which
# buries the interesting lines. So instead we take a *focused* approach:
#
#   - keep the framework generally quiet (WARNING), and
#   - log each tool call ourselves via the public hooks API
#     (BeforeToolCallEvent / AfterToolCallEvent — see ToolUseLogger below).
#
# Why hooks instead of enabling DEBUG on the SDK's tool-executor logger
# (strands.tools.executors)? That logger name is an implementation detail —
# the docs only guarantee the "strands" hierarchy, not specific module names —
# so an SDK upgrade could rename it and silently empty our log. Hooks are a
# documented public API: the log format stays under our control, and if an
# event were ever removed we'd get an ImportError at startup instead of
# silence.
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
    # Focused view: quiet framework. Tool calls are logged by ToolUseLogger
    # (hooks-based) below, so no SDK-internal DEBUG logger is needed.
    logging.getLogger("strands").setLevel(logging.WARNING)

# Keep noisy third-party loggers quiet so the agent's tool use stands out.
for noisy in ("botocore", "boto3", "urllib3"):
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
# The `current_time` tool ships with `strands-agents-tools`. To see exactly how
# a production-grade tool is written (the @tool decorator, the
# docstring/type-hint schema, argument handling and error reporting), read the
# original source on GitHub:
#   current_time: https://github.com/strands-agents/tools/blob/main/src/strands_tools/current_time.py
#   (browse the folder for the other built-in tools)
#     https://github.com/strands-agents/tools/tree/main/src/strands_tools
from strands_tools import current_time

import json
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import (
    AfterToolCallEvent,
    BeforeModelCallEvent,
    BeforeToolCallEvent,
)


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


# --- Hook: log each tool invocation --------------------------------------------
# This replaces relying on the SDK's internal tool-executor logger
# (strands.tools.executors._executor). BeforeToolCallEvent fires just before a
# tool runs (giving us the tool the model picked and the arguments it passed);
# AfterToolCallEvent fires when it completes (giving us the result status).
# Because hooks are a documented public API, this keeps working — with an
# unchanged log format — across SDK upgrades.
class ToolUseLogger(HookProvider):
    """Logs each tool the model picks, its arguments, and its result status."""

    def __init__(self, log: logging.Logger):
        self._log = log

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)

    def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        self._log.info(
            "TOOL CALL | tool=%s | input=%s",
            event.tool_use["name"],
            json.dumps(event.tool_use.get("input", {}), default=str),
        )

    def _on_after_tool_call(self, event: AfterToolCallEvent) -> None:
        self._log.info(
            "TOOL RESULT | tool=%s | status=%s",
            event.tool_use["name"],
            event.result.get("status"),
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


# --- Create agent with two tools ---
agent = Agent(
    model="amazon.nova-lite-v1:0",
    tools=[current_time, unit_converter],
    system_prompt=(
        "You are a helpful assistant."
    ),
    callback_handler=None,
    # PromptContextLogger logs the full prompt/context (tool catalog + messages)
    # sent to the model on every turn; ToolUseLogger logs each tool call and
    # its result via the public hooks API.
    hooks=[PromptContextLogger(prompt_logger), ToolUseLogger(logger)],
)

# The agent decides which tool(s) to use based on the question
print("=== Agent Chooses Tools Autonomously ===\n")
print(f"(tool-use logs are being written to: {LOG_FILE})\n")
logger.info("Each 'TOOL CALL' line below shows the tool the model selected "
            "and the arguments it passed; 'TOOL RESULT' shows how it went.")

response = agent("Convert 100 kilometers to miles.")
print(f"Q: Convert 100 km to miles\nA: {response}\n")

response = agent("What is the current time in UTC?")
print(f"Q: Current time in UTC\nA: {response}\n")

# --- Direct tool invocation (bypasses agent reasoning) ---
print("=== Direct Tool Invocation ===\n")
result = agent.tool.unit_converter(value=72, from_unit="fahrenheit", to_unit="celsius")
print(f"Direct call: 72°F → Celsius = {result}")
