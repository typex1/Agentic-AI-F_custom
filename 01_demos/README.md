# Module 3: Advanced Patterns

Multi-agent architectures, RAG (Retrieval-Augmented Generation), graphs, and swarms.

## Learning Path

| # | File | Concept | What you'll learn |
|---|------|---------|-------------------|
| 7a | `07_Retrieval_OKF.py` | RAG with files | Retrieve context from markdown knowledge files |
| 7b | `07_Retrieval_SQL.py` | RAG with SQL | NL2SQL — agent queries a database adaptively |
| 8 | `08_multi_agent.py` | Multi-agent | Agents-as-tools pattern for delegation |
| 9 | `09_graph.py` | Graphs | Deterministic star + fan-in topology |
| 11 | `11_swarm.py` | Swarms | Self-organizing team with handoffs |

## Prerequisites

```bash
pip install strands-agents strands-agents-tools
```

## Running

```bash
python 03-advanced-patterns/08_multi_agent.py
python 03-advanced-patterns/09_graph.py
python 03-advanced-patterns/11_swarm.py
```

## Key Concepts

### Agents-as-Tools (Multi-Agent)

One agent can call another as a tool — enabling specialization and delegation:

```python
researcher = Agent(system_prompt="You are a researcher...")
writer = Agent(system_prompt="You are a writer...", tools=[researcher.as_tool()])
```

### Graph Workflows

For deterministic orchestration, graphs let you define explicit node-to-node routing:

```
Coordinator → [Researcher, Analyst, Writer] → Aggregator → Done
```

### Swarms

Swarms are self-organizing: agents hand off to each other dynamically based on the task, without a fixed topology.

## Data Files

- `OKF_data/` — Markdown knowledge files used by the RAG retrieval demo
- `knowledgebase/` — Domain-specific documents (Deutsche Bahn timetable data)
- `data/wealthmanagement.db` — SQLite database for the NL2SQL demo
