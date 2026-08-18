# Module 4: Production Readiness

Session persistence and conversation management — keeping agents stateful and context-efficient.

## Learning Path

| # | File | Concept | What you'll learn |
|---|------|---------|-------------------|
| 10 | `10_session_management.py` | Sessions | Persist and resume conversations across invocations |
| 12 | `12_conversation_management.py` | Context management | Sliding-window, null, and summarizing history managers |

## Prerequisites

```bash
pip install strands-agents strands-agents-tools
```

## Running

```bash
python 04-production/10_session_management.py
python 04-production/12_conversation_management.py
```

## Key Concepts

### Session Management

Agents are stateless by default. Session managers let you save and restore conversation state:

```python
from strands import Agent
from strands.session import FileSessionManager

session_mgr = FileSessionManager(session_dir="./sessions")
agent = Agent(session_manager=session_mgr)
```

### Conversation Management

As conversations grow, the context window fills up. Conversation managers handle this:

| Strategy | Behavior |
|----------|----------|
| **Sliding window** | Keep only the last N messages |
| **Summarizing** | Compress older messages into a summary |
| **Null** | No management — fail when context is full |

## Also See

The reference course covers these topics in more depth:
- [09-persistent-memory](../reference/building-with-strands-course/samples/09-persistent-memory/) — File and S3 session managers
- [08-conversation-management](../reference/building-with-strands-course/samples/08-conversation-management/) — All context strategies
- [14-deploy](../reference/building-with-strands-course/samples/14-deploy/) — AgentCore + Lambda deployment
