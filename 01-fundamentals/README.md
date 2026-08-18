# Module 1: Fundamentals

Learn the core concepts of the Strands Agents SDK — from calling Bedrock directly to creating agents with structured output.

## Learning Path

| # | File | Concept | What you'll learn |
|---|------|---------|-------------------|
| 0 | `00_bedrock_direct.py` | Raw Bedrock API | How the Converse API works without any framework |
| 1 | `01_basic_agent.py` | Simplest agent | 3 lines of code → working AI agent |
| 2 | `02_custom_tools.py` | Custom tools | The `@tool` decorator — turn any function into an agent-callable tool |
| 3 | `03_logging.py` | Observability | See the tool catalog, prompts, and context in logs |
| 4 | `04_structured_output.py` | Typed output | Get validated Pydantic models back from agents |

## Prerequisites

```bash
pip install strands-agents strands-agents-tools pydantic
```

## Running

```bash
# From the repo root:
python 01-fundamentals/01_basic_agent.py
```

Each file is self-contained and runnable independently.

## Key Concepts

### The Agent Loop

```
User prompt → Model reasoning → Tool selection → Tool execution → Model response
                    ↑_________________________________↓ (loops until done)
```

### The @tool Decorator

```python
from strands import Agent, tool

@tool
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    return f"It's sunny in {location}"

agent = Agent(tools=[get_weather])
agent("What's the weather in Berlin?")
```

## Log Output

The `logs/` directory contains sample output from `03_logging.py` showing the full agent reasoning trace.
