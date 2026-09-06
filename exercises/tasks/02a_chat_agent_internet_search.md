# Task: add internet search 

Add internet/web search using the DDGS (Duck Duck Go Search), add this to the agent as a custom tool.

Be aware that agent tools, in order to really be well selected by the LLM, need precise tool descriptions.
For example, find the extracted Kiro tool description for "web_search" here: https://github.com/dwalleck/cyril/blob/2e56ed603ea3685ceb656dfdc4ec515cfd659d93/docs/kiro-embedded/context-entry-system.md?plain=1#L660

## 📖 Official documentation

- [Python Tools (@tool decorator)](https://strandsagents.com/docs/user-guide/concepts/tools/python-tools/) — turn a plain Python function (like a DDGS search) into a custom tool
