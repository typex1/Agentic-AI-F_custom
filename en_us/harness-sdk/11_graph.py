"""
11_graph.py — Multi-Agent Graph (deterministic orchestration)

Adapted from the Strands Agents sample:
  strands-agents/samples → python/01-learn/12-graph

WHAT IT DOES
------------
An Agent Graph organizes agents into an explicit topology:
  * Nodes = agents with specific roles
  * Edges = communication paths (who feeds whom)
Unlike a Swarm (agents self-organize) the graph is DETERMINISTIC: you define
the flow, and outputs propagate along the edges in dependency order.

This builds a "star + fan-in" topology for market research:

        ┌──────────────┐
        │ coordinator  │  (entry: splits the brief)
        └──────┬───────┘
       ┌───────┼────────┐
       ▼       ▼        ▼
   market   tech    competitor      (three parallel analysts)
   analyst  analyst  analyst
       └───────┼────────┘
               ▼
          ┌─────────┐
          │ synth   │  (fans in, writes the final report)
          └─────────┘

ADAPTATION FOR THIS LIMITED-PERMISSION ENVIRONMENT
--------------------------------------------------
Per .kiro/steering/Permissions.md we only have `bedrock-runtime:Converse` on
`amazon.nova-lite-v1:0`. A Graph only needs model invocation, so it runs as-is;
we just pin every node agent to Nova Lite.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent
from strands.models import BedrockModel
from strands.multiagent import GraphBuilder

MODEL_ID = "amazon.nova-lite-v1:0"
AWS_REGION = "us-east-1"


def _model() -> BedrockModel:
    return BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.3)


def _agent(name: str, prompt: str) -> Agent:
    return Agent(name=name, model=_model(), system_prompt=prompt, callback_handler=None)


# --- Node agents ---
coordinator = _agent(
    "coordinator",
    "You break a market-research brief into clear sub-questions for three "
    "analysts: market size, technology, and competitors. Output a short brief "
    "for each. Be concise.",
)

market_analyst = _agent(
    "market_analyst",
    "You are a market-size analyst. Given the brief, estimate the market "
    "opportunity and key customer segments in 3-4 bullets.",
)

tech_analyst = _agent(
    "tech_analyst",
    "You are a technology analyst. Given the brief, summarize the key "
    "technologies and technical risks in 3-4 bullets.",
)

competitor_analyst = _agent(
    "competitor_analyst",
    "You are a competitive analyst. Given the brief, identify the main "
    "competitors and differentiation angles in 3-4 bullets.",
)

synthesizer = _agent(
    "synthesizer",
    "You are a strategy lead. Combine the market, technology, and competitor "
    "analyses into a concise go/no-go recommendation with a short rationale.",
)


def build_graph():
    builder = GraphBuilder()

    # Nodes
    builder.add_node(coordinator, "coordinator")
    builder.add_node(market_analyst, "market_analyst")
    builder.add_node(tech_analyst, "tech_analyst")
    builder.add_node(competitor_analyst, "competitor_analyst")
    builder.add_node(synthesizer, "synthesizer")

    # Edges: coordinator fans out to three analysts, who fan in to synthesizer
    builder.add_edge("coordinator", "market_analyst")
    builder.add_edge("coordinator", "tech_analyst")
    builder.add_edge("coordinator", "competitor_analyst")
    builder.add_edge("market_analyst", "synthesizer")
    builder.add_edge("tech_analyst", "synthesizer")
    builder.add_edge("competitor_analyst", "synthesizer")

    builder.set_entry_point("coordinator")
    return builder.build()


def main() -> None:
    graph = build_graph()
    task = (
        "Evaluate the opportunity for launching an AI-powered personal finance "
        "assistant for young professionals."
    )
    print("=== Multi-Agent Graph (star + fan-in) ===\n")
    print(f"Task: {task}\n")
    print("Running graph (deterministic flow along edges)...\n")

    result = graph(task)

    print("=" * 60)
    print(f"Status: {result.status}")
    order = " → ".join(node.node_id for node in result.execution_order)
    print(f"Execution order: {order}")
    print("=" * 60)


if __name__ == "__main__":
    main()
