"""
03_logging.py — Observing Tool Use Through Logging

A deliberately small setup — just two tools — with logging turned on so you
can *watch* the agent's tool-use decisions instead of just seeing the final
answer:
  - `current_time` (custom; Strands ships one in strands-agents-tools,
    CrewAI has no equivalent built-in, so we define it in a few lines)
  - `unit_converter` (custom, defined below with the @tool decorator)

Goal of this demo:
  - Watch each step of the agent loop: which tool the model picks, the
    arguments it passes, and the result that comes back
  - See the *actual prompt/context* sent to the model on every turn, to make a
    key point clear: tool use adds a lot of extra content to the context —
      * a "tools available" catalog (each tool's name, description and
        parameter schema) so the model knows what it can call, and
      * the growing conversation, where the model's chosen tool + populated
        parameters and each tool's output are fed back in so the model can
        reason over them.
  - Understand that "tool use" is just the model emitting a structured
    tool-call request, the framework executing your Python function, and
    feeding the result back into the conversation

How this differs from the Strands version:
  - Strands exposes a hooks API (BeforeToolCallEvent / AfterToolCallEvent /
    BeforeModelCallEvent) that you register per-agent via `hooks=[...]`.
  - CrewAI's equivalent is a global *event bus*: you subclass
    BaseEventListener and subscribe to typed events such as
    ToolUsageStartedEvent, ToolUsageFinishedEvent, and LLMCallStartedEvent.
    Same idea (documented public API, stable across upgrades), different
    wiring — listeners are registered on the bus, not on the agent.

The log is written to a file (crewai/logs/03_logging.log) instead of the
console. The file is truncated on every run so it only ever holds the most
recent execution.

Inspect the tool use with, e.g.:
    tail -f crewai/logs/03_logging.log
"""

import os
# Opt out of CrewAI telemetry/tracing before importing crewai (see 01_basic_agent.py).
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# --- Logging setup: file next to this script (crewai/logs/03_logging.log) ---
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "03_logging.log"

# Remove any log from a previous run so the file doesn't grow without bound.
LOG_FILE.unlink(missing_ok=True)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")],
)

# Keep noisy third-party loggers quiet so the agent's tool use stands out.
for noisy in ("botocore", "boto3", "urllib3", "LiteLLM", "httpx"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

# A logger of our own for tool-use narration.
logger = logging.getLogger("tool_use_demo")
logger.setLevel(logging.INFO)

# A dedicated logger for the prompt/context sent to the model — seeing the
# prompt is the whole point of this file.
prompt_logger = logging.getLogger("prompt_context")
prompt_logger.setLevel(logging.DEBUG)

from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from crewai.events import BaseEventListener
from crewai.events.types.llm_events import LLMCallStartedEvent
from crewai.events.types.tool_usage_events import (
    ToolUsageFinishedEvent,
    ToolUsageStartedEvent,
)


# --- Event listener: CrewAI's counterpart to Strands hooks ------------------
# BaseEventListener subclasses register callbacks on the global event bus.
# ToolUsageStartedEvent fires just before a tool runs (giving us the tool the
# model picked and the arguments it passed); ToolUsageFinishedEvent fires when
# it completes. LLMCallStartedEvent fires before every model inference and
# carries the full message list — the exact moment the prompt (system prompt +
# tool catalog + running history) is about to be sent.
class ToolUseLogger(BaseEventListener):
    """Logs each tool the model picks, its arguments, its result, and the
    full prompt/context sent to the model each turn."""

    def __init__(self, log: logging.Logger, prompt_log: logging.Logger):
        super().__init__()
        self._log = log
        self._prompt_log = prompt_log
        self._tools_logged = False

    def setup_listeners(self, crewai_event_bus) -> None:
        bus = crewai_event_bus
        @bus.on(ToolUsageStartedEvent)
        def on_tool_started(source, event: ToolUsageStartedEvent):
            self._log.info(
                "TOOL CALL | tool=%s | input=%s",
                event.tool_name,
                json.dumps(event.tool_args, default=str),
            )

        @bus.on(ToolUsageFinishedEvent)
        def on_tool_finished(source, event: ToolUsageFinishedEvent):
            self._log.info(
                "TOOL RESULT | tool=%s | from_cache=%s | output=%s",
                event.tool_name,
                event.from_cache,
                str(event.output)[:200],
            )

        @bus.on(LLMCallStartedEvent)
        def on_llm_call(source, event: LLMCallStartedEvent):
            # (1) The "tools available" catalog. Identical on every turn, so we
            # log it once — it's the extended content that teaches the model
            # which tools exist and what parameters each one accepts.
            if not self._tools_logged and event.tools:
                self._prompt_log.debug(
                    "TOOL CATALOG injected into every request (%d tools):\n%s",
                    len(event.tools),
                    json.dumps(event.tools, indent=2, default=str),
                )
                self._tools_logged = True

            # (2) The prompt actually sent this turn: system prompt plus the
            # running message history. As the loop progresses you'll see it
            # grow with the model's tool picks and the tool results fed back in.
            self._prompt_log.debug(
                "PROMPT SENT TO MODEL — %d message(s):\n%s",
                len(event.messages) if event.messages else 0,
                json.dumps(event.messages, indent=2, default=str),
            )


# Instantiating the listener registers it on the global event bus.
tool_use_logger = ToolUseLogger(logger, prompt_logger)


# --- Custom tool: current time (built-in in Strands; custom here) ---
@tool("current_time")
def current_time(tz: str = "UTC") -> str:
    """Get the current date and time.

    Args:
        tz: Timezone name; only 'UTC' is supported in this demo.

    Returns:
        The current date and time as an ISO-8601 string.
    """
    return datetime.now(timezone.utc).isoformat()


# --- Custom tool: just a decorated Python function ---
@tool("unit_converter")
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
llm = LLM(model="bedrock/amazon.nova-lite-v1:0")

agent = Agent(
    role="Helpful Assistant",
    goal="Answer questions, using tools when they help.",
    backstory="You are a helpful assistant.",
    tools=[current_time, unit_converter],
    llm=llm,
    verbose=False,
)

# The agent decides which tool(s) to use based on the question
print("=== Agent Chooses Tools Autonomously ===\n")
print(f"(tool-use logs are being written to: {LOG_FILE})\n")
logger.info("Each 'TOOL CALL' line below shows the tool the model selected "
            "and the arguments it passed; 'TOOL RESULT' shows how it went.")

for label, question in [
    ("Convert 100 km to miles", "Convert 100 kilometers to miles."),
    ("Current time in UTC", "What is the current time in UTC?"),
]:
    task = Task(
        description=question,
        expected_output="A concise answer based on the tool results.",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    print(f"Q: {label}\nA: {result}\n")

# --- Direct tool invocation (bypasses agent reasoning) ---
print("=== Direct Tool Invocation ===\n")
result = unit_converter.run(value=72, from_unit="fahrenheit", to_unit="celsius")
print(f"Direct call: 72°F → Celsius = {result}")
