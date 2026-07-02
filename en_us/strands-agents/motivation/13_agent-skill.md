# 13 — Agent Skill Integration

**Python file:** [`../13_agent-skill.py`](../13_agent-skill.py)

## Learning objective
Give an agent on-demand access to a self-contained package of specialized
instructions — a "skill" — without bloating the base system prompt, by
integrating a real community skill (Anthropic's **frontend-design**).

## Why it matters
As agents take on more domains, cramming every instruction into one prompt
causes context bloat, instruction confusion, and maintenance pain. Skills solve
this with **progressive disclosure**: the model only sees a lightweight menu
(name + description) until it decides a skill is relevant and activates it. It
also lets you reuse the growing ecosystem of open Agent Skills instead of
re-authoring domain expertise.

## What this example demonstrates
- Vendoring an external skill (Anthropic's `frontend-design` `SKILL.md`) into a
  local `skills/frontend-design/` directory.
- Registering it with the `AgentSkills` plugin (`plugins=[AgentSkills(...)]`).
- **Discovery**: listing the metadata injected into the system prompt via
  `plugin.get_available_skills()`.
- **Activation**: the agent calling the auto-provided `skills` tool to load the
  full instructions when a matching design task arrives.
- Providing `file_read` so the agent can access any bundled skill resources.
- Confirming activation with `plugin.get_activated_skills(agent)`.

## Key concepts
`AgentSkills` plugin, the Agent Skills specification, `SKILL.md` (YAML
frontmatter + markdown), progressive disclosure, the `skills` activation tool,
resource-access tools (`file_read`/`shell`), `get_available_skills` /
`get_activated_skills`.
