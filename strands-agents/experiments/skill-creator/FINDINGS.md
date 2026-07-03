# skill-creator try-out — findings

Notes from actually running Anthropic's [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
skill in *this* environment (Strands Agents + Amazon Nova Lite, single agent,
no subagents/browser/`claude` CLI). These notes back the student task in
[`../../tasks/5-skill-creator.md`](../../tasks/5-skill-creator.md).

## What this folder contains

| Path | What it is |
|------|------------|
| `skill-creator/` | The skill, vendored from GitHub (all 18 files: `SKILL.md`, `scripts/`, `agents/`, `references/`, `eval-viewer/`, `assets/`). |
| `try_skill_creator.py` | Strands runner: loads the skill via `AgentSkills` on Nova Lite (mirrors demo `13_agent-skill.py`) and drives it to author a new skill, then validates the result. |
| `generated/commit-message-writer/SKILL.md` | The skill Nova Lite produced (final, validated version). |

Run it: `python try_skill_creator.py`

## What skill-creator actually is

A **meta-skill** for authoring, evaluating, and improving *other* skills. Its
intended full loop:

```
draft SKILL.md
  -> run skill vs. baseline on test prompts (parallel subagents)
  -> grade assertions -> aggregate benchmark (pass rate, tokens, latency, variance)
  -> review qualitatively in a browser eval-viewer
  -> improve -> repeat
  -> optimize the trigger `description` (run_loop.py, uses `claude -p`)
  -> package as a .skill file
```

It bundles executable helpers (`scripts/`), subagent role prompts (`agents/`),
JSON schemas (`references/schemas.md`), and an HTML viewer (`eval-viewer/`). The
`SKILL.md` alone is ~33 KB.

## Key finding 1 — most of the skill can't run as-written here

The eval/benchmark/optimization half assumes **subagents**, a **browser/display**,
and the **`claude` CLI**. Our environment has none. So on Nova Lite only this
slice is genuinely reproducible:

- **Discovery** — the skill's metadata is injected into the system prompt.
- **Activation** — the agent calls the auto-provided `skills` tool (progressive
  disclosure loads the full instructions).
- **Authoring** — the agent follows the "Write the SKILL.md" guidance and writes
  a file.
- **Lightweight validation** — using the skill's *own* bundled
  `scripts/quick_validate.py` as a stand-in for the heavy eval loop.

## Key finding 2 — `AgentSkills` discovery needs the agent

Filesystem skills load **per-agent at `init_agent` time**, not at plugin
construction. Consequences:

- `plugin.get_available_skills()` with no argument returns `[]` (only
  Skill-instance/URL sources show up there).
- You must call `plugin.get_available_skills(agent)` *after* the agent has been
  initialised. In the runner we force this with
  `asyncio.run(skills_plugin.init_agent(agent))` before printing discovery.
- Demo `13_agent-skill.py` has the same latent gotcha — its discovery print
  would come up empty for the same reason.

Source: `strands/vended_plugins/skills/agent_skills.py` (`get_available_skills`
docstring and `_load_skill_paths`).

## Key finding 3 — Nova Lite drafts the shape but drops the mechanics

Observed, reproducibly:

- **Iteration 1 (draft):** activation succeeded (`activated_skills == ['skill-creator']`),
  but validation **FAILED**: `No YAML frontmatter found`. Nova Lite wrote a
  `## Description` markdown heading instead of the required `---` YAML
  frontmatter. That frontmatter (`name` + `description`) is literally the
  triggering mechanism, so this is a substantive defect, not cosmetic.
- **Iteration 2 (correction):** feeding the validator's exact error back to the
  agent produced a **PASS** (`Skill is valid!`), with correct frontmatter plus a
  usage section and two Input/Output examples.

This author → validate → correct micro-loop is a Nova-Lite-sized version of
exactly what skill-creator does at full scale. Takeaway: a smaller model can
follow authoring *guidance* but reliably needs a *validation gate* to catch the
mechanical requirements — which is the whole reason skill-creator is built around
evaluation.

## Implications for the student task

- Teach the **concepts** (progressive disclosure; frontmatter as the trigger;
  the draft → evaluate → improve loop) rather than the full subagent/benchmark
  machinery, which won't run here.
- Have students use `quick_validate.py` as their objective gate, and *observe*
  the model omitting frontmatter on the first pass — it makes the "why evaluate?"
  lesson land.
- Point interested students at the parts we can't run (`run_loop.py`,
  `generate_review.py`, `agents/*.md`) as "here's what this looks like at scale
  on Claude with subagents."
