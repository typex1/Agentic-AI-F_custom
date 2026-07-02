"""
00_landing_page_example.py — Agent + Tool + Guardrail Hook (landing page demo)

Demonstrates the "few lines of code" pitch from the landing page in Python:
  - A custom tool created with the @tool decorator (save_report)
  - An agent that autonomously decides to call the tool
  - A BeforeToolCallEvent hook acting as a guardrail: it cancels the tool
    call unless the report includes source citations ("[source]")

This is the Python (strands-agents) equivalent of the TypeScript snippet
shown on the landing page.

ENVIRONMENT NOTES / LIMITATIONS (per this repo's README):
  - Uses Amazon Bedrock with the Amazon Nova Lite model
    (amazon.nova-lite-v1:0) in us-east-1.
  - Requires bedrock-runtime:Converse permissions.
  - Reports are written to a local ./reports directory next to this script,
    instead of a hard-coded relative path, so the demo is safe to run from
    anywhere.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import re
from pathlib import Path

from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent

# Reports land in ./reports next to this script (created on demand).
REPORTS_DIR = Path(__file__).parent / "reports"


# --- Custom tool: a decorated Python function ---
@tool
def save_report(title: str, content: str) -> str:
    """Save a research report to disk as a Markdown file.

    Args:
        title: A short report title. Used to derive the filename.
        content: The full report body in Markdown. Must include source
            citations (a "[source]" marker) or the guardrail will reject it.

    Returns:
        A confirmation message with the saved file path.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # Sanitize the title into a safe filename.
    safe_name = re.sub(r"[^\w\-]+", "_", title).strip("_") or "report"
    path = REPORTS_DIR / f"{safe_name}.md"
    path.write_text(content, encoding="utf-8")
    return f"Saved {path.name} ({len(content)} chars) to {path.parent}"


# --- Guardrail hook: block saves that lack source citations ---
def require_citations(event: BeforeToolCallEvent) -> None:
    """Cancel save_report calls whose content has no '[source]' citation.

    The event type is inferred from the type hint, so this can be registered
    with a bare agent.add_hook(require_citations).
    """
    if event.tool_use["name"] != "save_report":
        return

    content = event.tool_use["input"].get("content", "")
    if "[source]" not in content:
        # cancel_tool short-circuits execution and feeds this message back
        # to the model so it can correct the report and try again.
        event.cancel_tool = (
            "Report rejected: add source citations. Every claim must be "
            "followed by a '[source]' marker before the report can be saved."
        )


# --- Wire up the agent (a handful of lines) ---
agent = Agent(
    model="amazon.nova-lite-v1:0",
    tools=[save_report],
    system_prompt=(
        "You are a research assistant. When asked to research a topic, write a "
        "concise report (a few bullet points is fine) and save it using the "
        "save_report tool. Cite every claim with a '[source]' marker."
    ),
    callback_handler=None,  # Suppress streaming; we print the final result.
)

# Register the guardrail hook.
agent.add_hook(require_citations)

# The agent decides on its own to call save_report; the hook enforces citations.
print("=== Landing Page Demo: Agent + Tool + Guardrail Hook ===\n")
response = agent("Research AI agent frameworks and save a short report.")
print(response)

# Show what (if anything) was written to disk.
print("\n=== Saved Reports ===")
if REPORTS_DIR.exists() and any(REPORTS_DIR.iterdir()):
    for report in sorted(REPORTS_DIR.glob("*.md")):
        print(f"- {report}")
else:
    print("(no reports saved)")
