# Task: add tool calls 

The **Strands Agents SDK** has some built-in tools, see 
https://github.com/strands-agents/tools/tree/main/src/strands_tools for details.

From the above tool list, add file-read and file-write to our agent.
Also add the `bash` tool vended by strands-agents itself
(`from strands.vended_tools import bash`) for running shell commands —
note: the older `shell` tool from strands_tools is deprecated.

## 📖 Official documentation

- [Community Tools Package](https://strandsagents.com/docs/user-guide/concepts/tools/community-tools-package/) — the built-in `strands_tools` used in this task
- [Python Tools](https://strandsagents.com/docs/user-guide/concepts/tools/python-tools/) — how tools plug into an agent
