"""
10_swarm.py — Multi-Agent Swarm

Adapted from the Strands Agents sample:
  strands-agents/samples → python/01-learn/11-swarm

WHAT IT DOES
------------
A Swarm is a *collaborative* multi-agent pattern: several specialized agents
share working memory and hand off to each other autonomously — no central
orchestrator decides the order. Each agent decides when to pass control to a
teammate better suited to the next step.

This complements 05_multi_agent.py (agents-as-tools, where one agent explicitly
calls others): here the agents self-organize as a team.

We build a small software-delivery swarm:
  researcher → architect → coder → reviewer   (order emerges at runtime)

The swarm supports arbitrary handoff chains — including loops and back-and-forth patterns like your example. The framework has no structural restriction on which agent hands off to
  which.
  
  To get reviewer → coder → architect, you'd just adjust the prompts. For example:
  
  - Tell the reviewer: "If you find significant design flaws, hand off to 'architect'. If you find only implementation bugs, hand off to 'coder'. If everything is acceptable, STOP."
  - Tell the coder: "After fixing, hand off back to 'reviewer'."
  - Tell the architect: "After redesigning, hand off to 'coder'."

ADAPTATION FOR THIS LIMITED-PERMISSION ENVIRONMENT
--------------------------------------------------
Per .kiro/steering/Permissions.md we only have `bedrock-runtime:Converse` on
`amazon.nova-lite-v1:0`. A Swarm only needs model invocation, so it runs as-is;
we just pin every agent to Nova Lite instead of the default Claude Sonnet 4.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent
from strands.models import BedrockModel
from strands.multiagent import Swarm

MODEL_ID = "amazon.nova-lite-v1:0"
AWS_REGION = "us-east-1"


def _model() -> BedrockModel:
    return BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.3)


# --- Specialized agents (each gets a name so teammates can hand off to it) ---
researcher = Agent(
    name="researcher",
    model=_model(),
    system_prompt=(
        "You are ONLY a requirements researcher. Your single job: write a short "
        "bulleted list of the key requirements for the task. You must NOT design, "
        "write code, or review. As soon as you have listed requirements, you MUST "
        "hand off to the 'architect' agent to design the solution."
    ),
    callback_handler=None,
)

architect = Agent(
    name="architect",
    model=_model(),
    system_prompt=(
        "You are ONLY a software architect. Your single job: given the "
        "requirements, describe a minimal design (components, endpoints, data "
        "flow) in a few bullets. You must NOT write full code or review. As soon "
        "as the design is described, you MUST hand off to the 'coder' agent."
    ),
    callback_handler=None,
)

coder = Agent(
    name="coder",
    model=_model(),
    system_prompt=(
        "You are ONLY a Python developer. Your single job: implement the "
        "architect's design as a short code sketch. You must NOT review your own "
        "work. As soon as the code sketch is written, you MUST hand off to the "
        "'reviewer' agent."
    ),
    callback_handler=None,
)

reviewer = Agent(
    name="reviewer",
    model=_model(),
    system_prompt=(
        "You are ONLY a code reviewer and the final agent. Review the coder's "
        "implementation for bugs and clarity, give a short verdict and at most two "
        "concrete suggestions, then provide the final summary and STOP. Do not "
        "hand off to anyone."
    ),
    callback_handler=None,
)

# --- Assemble the swarm (self-organizing team with shared context) ---
swarm = Swarm(
    [researcher, architect, coder, reviewer],
    max_handoffs=12,
    max_iterations=12,
    execution_timeout=300.0,
    node_timeout=120.0,
    repetitive_handoff_detection_window=8,
    repetitive_handoff_min_unique_agents=3,
)


def main() -> None:
    task = (
        "Design and implement a minimal REST API for a to-do list app "
        "(create, list, and complete tasks). Keep it small."
    )
    print("=== Multi-Agent Swarm ===\n")
    print(f"Task: {task}\n")
    print("Running swarm (agents hand off autonomously)...\n")

    result = swarm(task)

    print("=" * 60)
    print(f"Status: {result.status}")
    handoff_path = " → ".join(node.node_id for node in result.node_history)
    print(f"Handoff path: {handoff_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
