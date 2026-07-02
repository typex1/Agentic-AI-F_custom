"""
13_agent-skill.py — Integrating an Agent Skill

Demonstrates the Strands `AgentSkills` plugin by integrating Anthropic's
open-source **frontend-design** skill:
  https://github.com/anthropics/skills/tree/main/skills/frontend-design

WHAT IS AN AGENT SKILL?
-----------------------
A "skill" is a self-contained package of specialized instructions (a `SKILL.md`
file with YAML frontmatter + markdown) that follows the open Agent Skills
specification. The `AgentSkills` plugin uses *progressive disclosure*:

  1. Discovery — only the skill's lightweight metadata (name + description) is
     injected into the system prompt, so the context window stays lean.
  2. Activation — when the agent decides it needs the skill, it calls the
     auto-provided `skills` tool, which returns the FULL instructions.
  3. Execution — the agent follows those instructions (and can read any bundled
     resource files via tools you provide, e.g. file_read / shell).

This keeps deep, domain-specific knowledge out of the base prompt until it's
actually needed — and lets you reuse community skills like Anthropic's.

ADAPTATION FOR THIS LIMITED-PERMISSION ENVIRONMENT
--------------------------------------------------
Per .kiro/steering/Permissions.md we only have `bedrock-runtime:Converse` on
`amazon.nova-lite-v1:0`. Skills are a client-side concern (metadata + a tool
call), so this runs as-is on Nova Lite. The skill's SKILL.md is fetched from
GitHub on first run and cached locally next to this script (needs internet once).

Requires: strands-agents, strands-agents-tools, and internet on first run.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import urllib.request
from pathlib import Path

from strands import Agent, AgentSkills
from strands.models import BedrockModel
from strands_tools import file_read

MODEL_ID = "amazon.nova-lite-v1:0"
AWS_REGION = "us-east-1"

# The skill directory MUST be named after the skill (name validation).
BASE_DIR = Path(__file__).resolve().parent
SKILL_DIR = BASE_DIR / "skills" / "frontend-design"
SKILL_MD = SKILL_DIR / "SKILL.md"
SKILL_URL = (
    "https://raw.githubusercontent.com/anthropics/skills/main/"
    "skills/frontend-design/SKILL.md"
)


def ensure_skill() -> None:
    """Vendor Anthropic's frontend-design SKILL.md locally (once)."""
    if SKILL_MD.exists():
        return
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading frontend-design skill → {SKILL_MD} ...")
    with urllib.request.urlopen(SKILL_URL, timeout=30) as resp:
        SKILL_MD.write_bytes(resp.read())


def _model() -> BedrockModel:
    return BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.3)


def main() -> None:
    ensure_skill()

    # 1. Create the AgentSkills plugin pointing at the skill directory.
    skills_plugin = AgentSkills(skills=str(SKILL_DIR))

    # 2. Build an agent with the plugin. file_read lets the agent open any
    #    bundled resource files a skill lists on activation.
    agent = Agent(
        model=_model(),
        plugins=[skills_plugin],
        tools=[file_read],
        system_prompt=(
            "You are a helpful design assistant. You have access to specialized "
            "skills. When a task matches an available skill, activate it via the "
            "`skills` tool BEFORE answering, then follow its instructions."
        ),
        callback_handler=None,
    )

    # --- Discovery: the metadata the model sees in its system prompt ---
    print("=== Available Skills (metadata only, injected into prompt) ===")
    for skill in skills_plugin.get_available_skills():
        print(f"  • {skill.name}: {skill.description[:90]}...")
    print()

    # --- Activation + execution: ask a design question that needs the skill ---
    task = (
        "I'm building a landing page for a small-batch coffee roaster. "
        "Use your frontend-design skill to propose a distinctive visual "
        "direction: palette (named hex values), typography pairing, and the one "
        "signature element the page should be remembered by."
    )
    print("=== Task ===")
    print(task + "\n")
    print("=== Agent Response (activates the skill on demand) ===")
    response = agent(task)
    print(response)

    # --- Show which skills the agent actually activated (tracked in state) ---
    activated = skills_plugin.get_activated_skills(agent)
    print("\n=== Activated Skills ===")
    print(activated if activated else "(none — the model answered without activating)")


if __name__ == "__main__":
    main()
