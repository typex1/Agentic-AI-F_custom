# Task: give your agent a skill

Agent Skills package specialized instructions in a `SKILL.md` file that the
agent loads **on demand** (progressive disclosure) — knowledge lives outside
your code.

1. Create a skill directory `skills/pirate-support/` with a `SKILL.md`:
   YAML frontmatter (`name: pirate-support`, a one-line `description`) and a
   markdown body instructing the agent to answer support questions in pirate
   speak, always end with exactly one ship emoji, and sign off as
   "Cap'n Support". (Silly on purpose — you can *see* whether the skill fired.)
2. Load it with the `AgentSkills` plugin:
   `Agent(plugins=[AgentSkills(skills=["./skills/"])], ...)`.
3. Chat with the agent: a plain question ("What is MCP?") should stay normal;
   a support question should activate the skill. Watch for the agent calling
   its auto-provided `skills` tool.
4. Now change the SKILL.md instructions and re-run — behavior changes with
   **zero code changes**. That is the point of skills.

Skill names must match `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`.

Demo to study first: `02-tools-and-mcp/06_agent-skill.py` (loads Anthropic's
open-source frontend-design skill).

## 📖 Official documentation

- [Agent Skills plugin](https://strandsagents.com/docs/user-guide/concepts/plugins/skills/) — `AgentSkills`, SKILL.md format, progressive disclosure

## Skill examples, for inspiration

- Matt Pocock's collection on GitHub: https://github.com/mattpocock/skills/tree/main/skills
- For inspiration, you could check how Hermes Agent is even able to create agent skills dynamically: https://www.youtube.com/watch?v=wLB0EwEPWFo
