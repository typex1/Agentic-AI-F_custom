# The Agent Loop — visualized

The agent loop is the foundational concept in Strands: *invoke the model,
check if it wants a tool, run the tool, invoke the model again with the
result — repeat until the model produces a final response.*

This page visualizes the **"A Concrete Example"** section of the official
[Agent Loop](https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/)
documentation: an agent asked to *analyze a codebase for security
vulnerabilities* — a task no model can do from memory. It needs tools, and
it needs several rounds.

## The loop itself

```mermaid
flowchart LR
    A([Input & Context]) --> Loop
    subgraph Loop["Agent loop — repeats until stop reason = end_turn"]
        direction TB
        B["Reasoning (LLM)"] --> C{"Tool use<br/>requested?"}
        C -- yes --> D["Tool execution"]
        D -- "tool result appended<br/>to conversation history" --> B
    end
    C -- "no (end_turn)" --> E([Response])
```

Each pass through the loop adds to the conversation history. The model sees
not just the original request, but every tool it called and every result it
received — that accumulated context is what enables multi-step reasoning.

## The concrete example: five iterations

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant M as Model (LLM)
    participant T as Tool execution

    U->>M: "Analyze this codebase for security vulnerabilities"

    Note over M: Needs to understand the structure first
    M->>T: tool_use: list_files(repo_root)
    T-->>M: tool_result: directory structure

    Note over M: Identifies the main application entry point
    M->>T: tool_use: read_file(app entry point)
    T-->>M: tool_result: application code

    Note over M: Notices DB queries → suspects SQL injection
    M->>T: tool_use: read_file(database module)
    T-->>M: tool_result: database module code

    Note over M: Finds it: user input concatenated into SQL.<br/>How wide is the blast radius?
    M->>T: tool_use: search_code(vulnerable function)
    T-->>M: tool_result: 12 call sites

    Note over M: Has everything it needs → stop reason: end_turn
    M-->>U: Report: vulnerability, 12 affected locations, remediation steps
```

Iterations 1–4 end with stop reason **tool use** (the loop continues);
iteration 5 ends with **end turn** (the loop exits). The model chose each
step autonomously based on what it had learned so far.

## What the model sees each iteration

The conversation history grows with every turn — that is the model's working
memory for the task:

```mermaid
flowchart TD
    subgraph I1["Iteration 1"]
        direction LR
        a1["user: request"]
    end
    subgraph I2["Iteration 2"]
        direction LR
        b1["user: request"] --> b2["assistant: list_files"] --> b3["user: dir structure"]
    end
    subgraph I3["Iteration 3"]
        direction LR
        c1["…"] --> c2["assistant: read_file(entry)"] --> c3["user: app code"]
    end
    subgraph I4["Iteration 4"]
        direction LR
        d1["…"] --> d2["assistant: read_file(db)"] --> d3["user: db code"]
    end
    subgraph I5["Iteration 5"]
        direction LR
        e1["…"] --> e2["assistant: search_code"] --> e3["user: 12 call sites"] --> e4["assistant: FINAL REPORT"]
    end
    I1 --> I2 --> I3 --> I4 --> I5
```

Two roles only: **user** messages carry the request *and* every tool result;
**assistant** messages carry text, tool-use requests, and (when supported)
reasoning traces. Tool results are user messages — that is how the world
"talks back" to the model.

## Stop reasons — how the loop decides to continue or exit

```mermaid
flowchart TD
    INV["Model invocation ends"] --> SR{stop reason?}
    SR -- "tool_use" --> RUN["run tools, append results"] --> AGAIN["invoke model again"]
    SR -- "end_turn / stop_sequence" --> OK([normal exit: return final message])
    SR -- "limit_turns / limit_total_tokens /<br/>limit_output_tokens" --> LIM([graceful budget exit:<br/>history valid, re-invokable])
    SR -- "cancelled" --> CAN([stopped via agent.cancel])
    SR -- "max_tokens" --> ERR([error: truncated response,<br/>unrecoverable])
    SR -- "content_filtered /<br/>guardrail_intervention" --> BLK([blocked by safety policy])
```

## Try it in this repo

- [`01-fundamentals/02_custom_tools.py`](../01-fundamentals/02_custom_tools.py) —
  watch a single loop iteration with a tool call
- [`exercises/tasks/03_chat_agent_logging.md`](../exercises/tasks/03_chat_agent_logging.md) —
  log every tool call and *see* the iterations happen
- Cap the loop with `agent(prompt, limits={"turns": 3})` and check
  `result.stop_reason`

## 📖 Official documentation

- [Agent Loop](https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/) — the source of this example, plus stop reasons, cancellation, limits
- [Conversation Management](https://strandsagents.com/docs/user-guide/concepts/agents/conversation-management/) — keeping the growing history inside the context window
- [Hooks](https://strandsagents.com/docs/user-guide/concepts/agents/hooks/) — observe before/after each model call and tool execution
