# Reference Material

Complete course samples and official examples — kept here for reference and deep dives.

## Contents

### Building with Strands Course

**Path:** `building-with-strands-course/`

The full 14-module video course by Morgan Willis (AWS). Contains both the original `samples/` and locally adjusted `samples_adjusted/` versions.

[Course Playlist (YouTube)](https://www.youtube.com/playlist?list=PLDzwjhH-4yhU)

| Module | Topic |
|--------|-------|
| 01 | Agent harnesses and the agent loop |
| 02 | Swapping model providers |
| 03 | Tools, MCP servers, and tool filtering |
| 04 | Callbacks, streaming, and FastAPI |
| 05 | Lifecycle hooks and safety guardrails |
| 06 | Plugins and on-demand skills |
| 07 | Steering handlers and workflow enforcement |
| 08 | Context management and compression |
| 09 | Session managers for persistent memory |
| 10 | Multi-agent: agents as tools |
| 11 | Graphs and structured workflows |
| 12 | Agent swarms and shared context |
| 13 | Evaluating agents |
| 14 | Deploying to production (AgentCore + Lambda) |

### Strands Official Examples

**Path:** `strands-official-examples/`

Examples from the [strands-agents/samples](https://github.com/strands-agents/samples) repo, including a `python_lab2_adjusted/` variant with local modifications.

### Agent Evaluation

Evaluating an agent goes beyond "did it answer correctly?" — trajectory (right tools, right order), output quality, robustness, and cost/latency all matter. The course module 13 has complete runnable examples (LLM-as-a-judge, trajectory validation, experiment generators):

→ [`building-with-strands-course/samples/13-evals/`](building-with-strands-course/samples/13-evals/) — requires `strands-agents-evals` (already in `requirements.txt`)

### Research Reports

**Path:** `reports/` — background writeups comparing agent frameworks and their capabilities.

### Original Strands-Agents README

**Path:** `strands-agents-original-README.md` — the demo README before restructuring.
