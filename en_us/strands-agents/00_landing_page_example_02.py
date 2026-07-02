from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent / "reports"

@tool
def save_report(title: str, content: str) -> str:
    """Save a research report to disk."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{title}.md"
    path.write_text(content)
    return f"Saved {path}"

def require_sources(event: BeforeToolCallEvent):
    name = event.tool_use["name"]
    content = event.tool_use["input"].get("content", "")
    if name == "save_report" and "[source]" not in content:
        event.cancel_tool = "Add source citations."

agent = Agent(
    model="amazon.nova-lite-v1:0",  # this environment only permits Nova Lite (Bedrock, us-east-1)
    tools=[save_report],
    hooks=[require_sources],
    system_prompt=(
        "You are a research assistant. When asked to research a topic, write the "
        "report yourself and save it immediately with the save_report tool. "
        "Every claim must be followed by a '[source]' citation marker. "
        "This is a non-interactive script: never ask the user questions or for "
        "confirmation. Always call save_report before finishing."
    ),
)
agent("Research AI agent frameworks")