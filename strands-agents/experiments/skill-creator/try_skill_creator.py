"""
try_skill_creator.py — Trying out Anthropic's `skill-creator` skill on Nova Lite

This mirrors demo `06_agent-skill.py`, but points the Strands `AgentSkills`
plugin at Anthropic's **skill-creator** skill — a *meta-skill* whose job is to
help you author, evaluate, and optimize other skills.

WHAT WE CAN AND CANNOT DO HERE
------------------------------
skill-creator is written for Claude with **subagents**, a **browser-based eval
viewer**, and the **`claude` CLI** (`claude -p`). Its full loop is:
    draft -> spawn parallel with-skill/baseline runs -> grade -> benchmark ->
    review in browser -> improve -> repeat -> optimize description -> package.

Our environment is a *single* Nova Lite agent with no subagents, no browser, and
only `bedrock-runtime:Converse`. So we exercise the slice of the workflow a
single agent can genuinely do end-to-end:

  1. Discover the skill-creator skill (metadata in the system prompt).
  2. Activate it via the auto-provided `skills` tool (progressive disclosure
     loads the full instructions).
  3. Follow its SKILL.md-authoring guidance to draft a brand-new small skill and
     write it to disk with file_write.
  4. A *miniature* stand-in for skill-creator's eval loop: validate the draft
     with the skill's own bundled `scripts/quick_validate.py`, and if it fails,
     feed the validator's error back to the agent for one correction pass.

Everything heavier (subagent A/B runs, quantitative benchmarks, the browser
review viewer, description optimization via run_loop.py) is out of scope on Nova
Lite and is left to the write-up.

Requires: strands-agents, strands-agents-tools, PyYAML. No internet (the skill
is already vendored next to this file).
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import asyncio
import importlib.util
import os
from pathlib import Path

# The skill-creator SKILL.md tells the agent to run shell commands / scripts.
# Allow the built-in tools to run unattended for this experiment.
os.environ["BYPASS_TOOL_CONSENT"] = "true"

from strands import Agent, AgentSkills
from strands.models import BedrockModel
from strands_tools import file_read, file_write, shell

MODEL_ID = "amazon.nova-lite-v1:0"
AWS_REGION = "us-east-1"

BASE_DIR = Path(__file__).resolve().parent
# Directory name MUST equal the skill's `name` frontmatter (AgentSkills checks this).
SKILL_DIR = BASE_DIR / "skill-creator"
# Where we ask the agent to write the new skill it authors.
OUTPUT_DIR = BASE_DIR / "generated" / "commit-message-writer"
OUTPUT_MD = OUTPUT_DIR / "SKILL.md"

# Reuse the skill's OWN bundled validator as our lightweight "eval".
_VALIDATOR_PATH = SKILL_DIR / "scripts" / "quick_validate.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("quick_validate", _VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_skill


validate_skill = _load_validator()


def _model() -> BedrockModel:
    return BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.2)


TASK = f"""\
Use your skill-creator skill to help me author a brand-new skill.

IMPORTANT ENVIRONMENT CONSTRAINTS (read carefully):
- You are a single agent running on Amazon Nova Lite. You have NO subagents, NO
  browser/display, and NO `claude` CLI.
- SKIP the entire evaluation/benchmark/description-optimization loop (no
  run_eval.py, run_loop.py, generate_review.py, subagents, or feedback.json).
- Your deliverable is ONLY a well-formed SKILL.md draft written to disk. Follow
  the skill-creator's "Creating a skill -> Write the SKILL.md" and "Skill
  Writing Guide" sections for structure and description quality.

The new skill to create:
- name: commit-message-writer
- purpose: turn a plain-language description of a code change into a
  Conventional Commits message (e.g. "feat(auth): add JWT login").
- trigger: when the user wants help writing a git commit message.
- output: a single Conventional Commits subject line, optionally with a short body.

Steps:
1. Activate the skill-creator skill (call the `skills` tool) before anything else.
2. Draft SKILL.md following its guidance. It MUST begin with YAML frontmatter
   delimited by lines of exactly three dashes (---), containing `name` and a
   "pushy", trigger-rich `description`. Then a concise markdown body with an
   imperative instructions section and at least one Input/Output example.
3. Write the finished SKILL.md to exactly this path using file_write:
   {OUTPUT_MD}

Keep it small and self-contained. When done, briefly say what you created.
"""


def run_validation(label: str) -> bool:
    """Validate the produced skill with the skill's bundled validator."""
    ok, message = validate_skill(str(OUTPUT_DIR))
    status = "PASS" if ok else "FAIL"
    print(f"\n=== Validation ({label}): {status} — {message} ===")
    return ok


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    skills_plugin = AgentSkills(skills=str(SKILL_DIR))

    agent = Agent(
        model=_model(),
        plugins=[skills_plugin],
        tools=[file_read, file_write, shell],
        system_prompt=(
            "You are a skill-authoring assistant with access to specialized "
            "skills. When a task matches an available skill, activate it via the "
            "`skills` tool BEFORE acting, then follow its instructions. You are "
            "running on Amazon Nova Lite as a single agent: no subagents, no "
            "browser, no external CLIs. Prefer writing files with file_write."
        ),
        callback_handler=None,
    )

    # Filesystem skills load per-agent at init_agent time. Force that load now so
    # discovery reflects the vendored skill, and pass the agent to see them.
    asyncio.run(skills_plugin.init_agent(agent))

    print("=== Available skills (metadata injected into the prompt) ===")
    for skill in skills_plugin.get_available_skills(agent):
        print(f"  • {skill.name}: {skill.description[:100]}...")

    print("\n=== Task ===")
    print(TASK)

    print("=== Agent response (iteration 1: draft) ===")
    print(agent(TASK))

    activated = skills_plugin.get_activated_skills(agent)
    print(f"\n=== Activated skills: {activated or '(none)'} ===")

    # --- Miniature eval loop: validate, and correct once if needed ---
    if not run_validation("iteration 1") and OUTPUT_MD.exists():
        _, err = validate_skill(str(OUTPUT_DIR))
        fix_prompt = (
            f"The SKILL.md you wrote to {OUTPUT_MD} failed validation with this "
            f"error:\n\n    {err}\n\n"
            "Fix ONLY that problem and rewrite the complete file with file_write. "
            "Remember: a valid skill file must START with YAML frontmatter — a line "
            "of exactly `---`, then `name:` and `description:` keys, then a closing "
            "`---` line — BEFORE any markdown headings. Keep all the good content "
            "you already wrote; just add/repair the frontmatter."
        )
        print("\n=== Agent response (iteration 2: correction) ===")
        print(agent(fix_prompt))
        run_validation("iteration 2")

    print(f"\n=== Produced file: {OUTPUT_MD} (exists: {OUTPUT_MD.exists()}) ===")


if __name__ == "__main__":
    main()
