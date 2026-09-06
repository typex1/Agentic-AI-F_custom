"""
07_agent_skills.py — Loading an Agent Skill from a SKILL.md (Strands + Nova Lite)

Solution for exercises/tasks/07_agent_skills.md:
  - A local skill directory (07_skills/pirate-support/SKILL.md) defines a
    support-reply style — instructions live OUTSIDE the code.
  - The AgentSkills plugin injects only name+description into the system
    prompt; the agent pulls the full instructions on demand via its
    auto-provided `skills` tool (progressive disclosure).
  - A normal question stays normal; a support question activates the skill.

Run:
  python 07_agent_skills.py

Then edit 07_skills/pirate-support/SKILL.md (e.g. change the emoji) and run
again — behavior changes with zero code changes.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from pathlib import Path

from strands import Agent, AgentSkills

SKILLS_DIR = Path(__file__).parent / "07_skills"

agent = Agent(
    model="amazon.nova-lite-v1:0",  # the only model permitted in this environment
    system_prompt=(
        "You are a helpful assistant. Answer any question from your own "
        "knowledge. Skills only ADD style/behavior rules for specific "
        "situations — a question outside any skill is answered normally."
    ),
    plugins=[AgentSkills(skills=[str(SKILLS_DIR)])],
    callback_handler=None,
)

print("=== Normal question (skill should NOT fire) ===")
print(agent("In one sentence: why is the sky blue?"))
print()

print("=== Support question (skill SHOULD fire) ===")
print(agent("My coffee machine arrived broken and I want a replacement. What do I do?"))
