# 09 — Red Teaming

**Python file:** [`../09_red_teaming.py`](../09_red_teaming.py)

## Learning objective
Probe an agent's security boundaries with adversarial inputs and automatically
judge whether the boundary held — i.e., test an agent for safety, not just
correctness.

## Why it matters
Agents that can run tools (shell, file access, APIs) have real attack surface.
Red teaming systematically checks that guardrails and sandboxes cannot be talked
around. This is the safety counterpart to functional testing.

## What this example demonstrates
- A target agent whose file access is confined to a **strands-shell** sandbox
  (only `/artifacts/` is mounted).
- The Strands Evals red-team primitives: `AttackGoal`, `RedTeamConfig`,
  `RedTeamCase`, `RedTeamExperiment`, and the `AttackSuccessEvaluator` judge.
- A custom `AttackStrategy` that fires escalating sandbox-escape prompts, then an
  LLM judge deciding breach vs. blocked.
- A verified outcome: all escape attempts are **blocked**.

## Key concepts
Red teaming, attack goals/strategies, LLM-as-judge evaluation, sandbox boundary
testing, adapting an eval to a small model (Nova Lite) with a deterministic
attacker.
