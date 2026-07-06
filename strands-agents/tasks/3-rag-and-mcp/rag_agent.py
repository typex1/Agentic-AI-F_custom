"""
rag_agent.py — RAG agent grounded via a custom MCP server (Task 3).

Connects to kb_mcp_server.py (launched as a stdio subprocess), discovers its
`search_knowledge_base` tool, and answers questions grounded in retrieved
passages — citing the source of each fact and admitting when the answer is
not in the knowledge base.

Uses:
  - Amazon Nova Lite (amazon.nova-lite-v1:0) via Amazon Bedrock
  - MCPClient with stdio transport (as in demo 07)
  - BM25 lexical retrieval (no embedding model available)

NOTE: Retrieval is lexical (keyword/BM25), not vector-based, because this
environment only has bedrock-runtime:Converse access — no embedding models.
This is a valid RAG retriever; only the ranking method differs from vector search.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import sys
from pathlib import Path

from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
MODEL_ID = "amazon.nova-lite-v1:0"
AWS_REGION = "us-east-1"

# Path to the MCP server script (sibling file)
SERVER_PATH = Path(__file__).resolve().parent / "kb_mcp_server.py"

SYSTEM_PROMPT = (
    "You are a rail-travel assistant. Answer ONLY using facts returned by the "
    "search_knowledge_base tool. For every answer:\n"
    "  1. Call search_knowledge_base with a focused query.\n"
    "  2. Base your answer strictly on the returned passages — do not use outside "
    "knowledge or invent details.\n"
    "  3. Cite the [source: ...] id of each passage you used, in parentheses.\n"
    "  4. If the passages do not contain the answer, say: \"I don't know — this "
    "is not covered in the knowledge base.\" Do not guess.\n"
    "Be concise and helpful."
)


# --------------------------------------------------------------------------- #
# MCP Client setup
# --------------------------------------------------------------------------- #
def build_mcp_client() -> MCPClient:
    """Create an MCPClient that launches kb_mcp_server.py as a stdio subprocess."""
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command=sys.executable,
                args=[str(SERVER_PATH)],
            )
        )
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    client = build_mcp_client()

    # Everything that uses MCP tools must run INSIDE the `with` block —
    # the connection closes when it exits.
    with client:
        tools = client.list_tools_sync()
        print("=== Tools discovered from MCP server ===")
        for t in tools:
            print(f"  • {t.tool_name}")
        print()

        model = BedrockModel(
            model_id=MODEL_ID,
            region_name=AWS_REGION,
            temperature=0.0,
        )
        agent = Agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            callback_handler=None,
        )

        # --- Demo questions ------------------------------------------------ #
        questions = [
            # In-corpus: delay compensation (tickets.md)
            "My ICE train arrived 90 minutes late. How much compensation can I claim?",
            # In-corpus: pets (onboard.md)
            "Can I take a large dog on the train, and are there any conditions?",
            # In-corpus: luggage storage (facilities.md)
            "How do I store luggage at the station and how do I pay for it?",
            # OUT of corpus → must admit it doesn't know
            "What time does the last train from Cologne to Paris depart?",
        ]

        for q in questions:
            print(f"Q: {q}")
            response = agent(q)
            print(f"A: {response}")
            print("-" * 70)


if __name__ == "__main__":
    main()
