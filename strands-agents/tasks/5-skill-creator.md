# Task 5 — Use Anthropic's `skill-creator` to Author a Skill

## Goal

Learn what an **Agent Skill** is and how to author one, by using Anthropic's
open-source **`skill-creator`** skill — a *meta-skill* whose whole job is to help
you build, validate, and improve *other* skills.

You will load `skill-creator` into a Strands agent (on Nova Lite, exactly like
the demos), let the agent **activate** it, and use its guidance to author a brand
new small skill of your own. Then you'll put that skill through a lightweight
**validate → fix → re-validate** loop — a miniature version of the real
skill-creator workflow.

This builds directly on demo `05_agent-skill.py` (the `AgentSkills` plugin).
Read that demo first if you haven't.

## Background: what is a skill, and what is skill-creator?

A **skill** is a self-contained package of instructions — a `SKILL.md` file with
YAML frontmatter (`name` + `description`) plus a markdown body, optionally
bundled with `scripts/`, `references/`, and `assets/`. Skills use *progressive
disclosure*: only the lightweight metadata sits in the prompt until the agent
decides it needs the skill and activates it via the `skills` tool.

**`skill-creator`** (https://github.com/anthropics/skills/tree/main/skills/skill-creator)
is a skill that teaches an agent how to create skills. Its full workflow —
draft → run test prompts → grade → benchmark → review → improve → optimize the
trigger description → package — is built for Claude with **subagents**, a
**browser eval-viewer**, and the **`claude` CLI**.

> **Reality check for this environment.** We run a *single* Nova Lite agent with
> no subagents, no browser, and no `claude` CLI. So the heavy evaluation and
> benchmarking half of `skill-creator` will NOT run here. That's fine — this task
> targets the part that does: discovery, activation, authoring, and a lightweight
> validation gate. A worked reference lives in
> [`../experiments/skill-creator/`](../experiments/skill-creator/) (see its
> `FINDINGS.md`).

## What you build

A script, `use_skill_creator.py`, that:

1. Vendors the `skill-creator` skill locally (or reuses the copy under
   `../experiments/skill-creator/skill-creator/`).
2. Builds a Strands agent on `amazon.nova-lite-v1:0` with the `AgentSkills`
   plugin pointed at that skill, plus `file_read` / `file_write` tools.
3. Prints the **discovered** skills, then asks the agent to **activate**
   `skill-creator` and **author a new skill of your choice** — write its
   `SKILL.md` to disk.
4. **Validates** the produced `SKILL.md` with the skill's own bundled
   `scripts/quick_validate.py`. If it fails, feed the error back to the agent and
   let it correct the file, then re-validate.

Pick any small, well-scoped skill to author. Some ideas: a Conventional Commits
message writer, a regex-explainer, a `.gitignore` generator, a SQL-to-natural-
language explainer. Keep it tiny.

## Functional requirements

- The agent uses **only** Nova Lite (`amazon.nova-lite-v1:0`).
- Your script prints the list of **available** skills (discovery) before running
  the authoring task.
- The agent **activates** `skill-creator` (verify via
  `plugin.get_activated_skills(agent)` — it should include `"skill-creator"`).
- A `SKILL.md` is written to disk for your new skill.
- The final `SKILL.md` **passes** `quick_validate.py`.
- If the first draft fails validation, your script does at least one automated
  **correction pass** driven by the validator's error message.

## Building blocks you already have

| Source | What to borrow |
|--------|----------------|
| `strands-agents/05_agent-skill.py` | The `AgentSkills` plugin: `AgentSkills(skills=<dir>)`, `plugins=[...]`, `get_available_skills(...)`, `get_activated_skills(agent)`. Vendoring a skill's `SKILL.md` from GitHub. |
| `skill-creator/SKILL.md` | The authoring guidance the agent will follow — read "Creating a skill → Write the SKILL.md" and the "Skill Writing Guide". |
| `skill-creator/scripts/quick_validate.py` | Your objective validation gate. Run it as `python quick_validate.py <skill_dir>`; import `validate_skill(path)` to call it in code. |

## Hints and gotchas (learned the hard way)

- **Discovery needs the agent.** Filesystem skills load *per-agent* at
  `init_agent` time. `plugin.get_available_skills()` with no argument returns an
  empty list — you must pass the agent: `get_available_skills(agent)`, and only
  after init. You can force loading with
  `asyncio.run(plugin.init_agent(agent))` before printing. (Demo 05 has this same
  latent quirk.)
- **The skill directory name must equal the skill's `name` frontmatter** — the
  plugin checks this. `skill-creator/` must contain a `SKILL.md` whose
  `name: skill-creator`.
- **Expect the first draft to be wrong.** On Nova Lite the first draft commonly
  **omits the YAML frontmatter** entirely (it writes a `## Description` heading
  instead). Since the frontmatter *is* the triggering mechanism, this fails
  validation — which is exactly why the validate→fix loop matters. Don't be
  surprised; catch it and correct it.
- `quick_validate.py` needs `PyYAML` (already in `requirements.txt`).
- Set `os.environ["BYPASS_TOOL_CONSENT"] = "true"` if you want `file_write` /
  `shell` to run unattended.

## Acceptance criteria

- [ ] Running the script prints the discovered `skill-creator` skill.
- [ ] `get_activated_skills(agent)` contains `"skill-creator"`.
- [ ] A `SKILL.md` for your chosen skill is written to disk.
- [ ] The final `SKILL.md` passes `quick_validate.py` (exit 0, "Skill is valid!").
- [ ] If the first draft failed, the transcript shows an automated correction
      pass that fixed it.

## Stretch goals (optional)

- Actually *use* the skill you authored: load it via `AgentSkills` in a second
  agent and give it a matching prompt; confirm it activates and produces the
  intended output.
- Write your own richer validator (e.g., require at least one Input/Output
  example, or a non-empty instructions section) and use it as the gate.
- Read `skill-creator/references/schemas.md` and sketch — on paper — the
  `evals.json` / `grading.json` / `benchmark.json` you *would* produce if you had
  subagents. What would each assertion check?
- Improve the `description` by hand for better "triggering": make it specific and
  a little "pushy" about when to use the skill, and argue why your wording
  triggers more reliably.

## Reflection questions

1. What is progressive disclosure, and why does it matter for the context window
   as the number of available skills grows?
2. Why is the `description` frontmatter the single most important field? What
   makes a description trigger reliably vs. under-trigger?
3. Nova Lite drafted the *shape* of a skill but dropped a mechanical requirement
   (the frontmatter). What does that tell you about why `skill-creator` is built
   around *evaluation* rather than one-shot generation?
4. Which parts of `skill-creator` could you only run with subagents / a browser /
   the `claude` CLI, and why? What would you need to change to run them here?
