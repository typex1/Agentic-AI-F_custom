# Module 5: Evaluation

Techniques and reports for evaluating AI agent quality.

## Contents

| Path | Description |
|------|-------------|
| `reports/` | Research reports on AI agent frameworks |

## Key Concepts

Agent evaluation goes beyond "did it answer correctly?" — you need to assess:

- **Trajectory** — Did the agent take a reasonable path? (right tools, right order)
- **Output quality** — Is the final answer correct, complete, well-formatted?
- **Robustness** — Does it handle edge cases, adversarial inputs, noisy data?
- **Cost/latency** — How many tokens/API calls did it use?

## Deep Dive: Course Evaluation Module

The reference course has a complete evaluation module with runnable code:

→ [reference/building-with-strands-course/samples/13-evals/](../reference/building-with-strands-course/samples/13-evals/)

Covers:
- LLM-as-a-judge evaluators
- Trajectory validation
- Customer service evaluation scenarios
- Experiment generators for systematic testing

```bash
pip install strands-agents-evals
```

## Reports

The `reports/` directory contains research writeups comparing agent frameworks and their capabilities.
