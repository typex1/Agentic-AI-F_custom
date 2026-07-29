"""
rag_agent.py — RAG agent grounded via your own MCP server (Task 3 reference)

Connects to the thin MCP server in kb_mcp_server.py (launched as a stdio
subprocess), discovers its `search_knowledge_base` tool, and answers questions
grounded in the retrieved passages — citing the source of each fact, and
admitting when the answer is not in the knowledge base.

This mirrors demo 05 (consuming an MCP server) but against a server we built
ourselves, and adds the RAG discipline of grounding + citation.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import sys
from pathlib import Path

from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

MODEL_ID = "amazon.nova-lite-v1:0"
AWS_REGION = "us-east-1"

SERVER_PATH = Path(__file__).resolve().parent / "kb_mcp_server.py"

SYSTEM_PROMPT = (
    "You are a rail-travel assistant. Answer ONLY using facts returned by the "
    "search_knowledge_base tool. For every answer:\n"
    "  1. Call search_knowledge_base with a focused query.\n"
    "  2. Base your answer strictly on the returned passages — do not use outside "
    "knowledge or invent details.\n"
    "  3. Cite the [source: ...] id of each passage you used, in parentheses.\n"
    "  4. If the passages do not contain the answer, say you don't know because it "
    "is not in the knowledge base. Do not guess.\n"
    "Be concise."
)


def build_mcp_client() -> MCPClient:
    """MCPClient that launches kb_mcp_server.py as a stdio subprocess."""
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command=sys.executable, args=[str(SERVER_PATH)])
        )
    )


def main() -> None:
    client = build_mcp_client()

    # Everything that uses MCP tools must run INSIDE the `with` block.
    with client:
        tools = client.list_tools_sync()
        print("=== Tools discovered from our MCP server ===")
        for t in tools:
            print(f"  • {t.tool_name}")
        print()

        model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.0)
        agent = Agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            callback_handler=None,
        )

        questions = [
            # in-corpus, needs a specific fact + citation
            "My ICE train arrived 90 minutes late. How much compensation can I claim?",
            # in-corpus, different document
            "Can I take a large dog on the train, and are there any conditions?",
            # in-corpus, facilities
            "How do I store luggage at the station and how do I pay for it?",
            # OUT of corpus -> must admit it doesn't know
            "What time does the last train from Cologne to Paris depart?",
        ]

        for q in questions:
            print(f"Q: {q}")
            print(f"A: {agent(q)}\n{'-' * 70}")


if __name__ == "__main__":
    main()
