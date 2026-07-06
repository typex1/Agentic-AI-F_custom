"""
kb_mcp_server.py — Thin MCP server exposing a knowledge-base search tool.

Part of Task 3: RAG over a Knowledge Base via MCP Server.

This is a *separate process* — the RAG agent (rag_agent.py) launches it as a
stdio subprocess via MCPClient and calls the `search_knowledge_base` tool.

Retrieval is LEXICAL (BM25-style scoring), NOT vector-based, because this
environment has no embedding model (only bedrock-runtime:Converse on Nova Lite).
The RAG pattern (retrieve passages → ground → cite) is unchanged; only the
ranking method differs from a vector store.

The corpus lives in ./knowledge_base/*.md and is chunked by `## ` headings.
Each passage is tagged with a citable source id like "facilities.md#Luggage".

Run standalone for testing:  python kb_mcp_server.py
(Normally the agent starts it as a subprocess.)
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
KB_DIR = Path(__file__).resolve().parent / "knowledge_base"

mcp = FastMCP("station-knowledge-base")


# --------------------------------------------------------------------------- #
# Corpus loading + chunking
# --------------------------------------------------------------------------- #
def _tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokenizer."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _load_passages() -> list[dict]:
    """Load every .md file and chunk on '## ' headings.

    Returns list of {"source": "<file>#<heading>", "text": "<heading + body>"}.
    """
    passages: list[dict] = []
    for md in sorted(KB_DIR.glob("*.md")):
        raw = md.read_text(encoding="utf-8")
        # Split on level-2 headings, keeping heading with its body
        chunks = re.split(r"\n(?=## )", raw)
        for chunk in chunks:
            chunk = chunk.strip()
            # Skip the top-level title line if it's alone
            if not chunk or (chunk.startswith("# ") and "\n" not in chunk):
                continue
            heading_match = re.search(r"##\s+(.+)", chunk)
            heading = heading_match.group(1).strip() if heading_match else md.stem
            passages.append({"source": f"{md.name}#{heading}", "text": chunk})
    return passages


# Load corpus at import time (server startup)
_PASSAGES = _load_passages()

# Precompute token lists for BM25
_DOC_TOKENS = [_tokenize(p["text"]) for p in _PASSAGES]
_N = max(len(_PASSAGES), 1)
_AVGDL = (sum(len(t) for t in _DOC_TOKENS) / _N) if _PASSAGES else 0.0


# --------------------------------------------------------------------------- #
# BM25 scoring
# --------------------------------------------------------------------------- #
def _idf(term: str) -> float:
    """Inverse document frequency with +1 smoothing (non-negative)."""
    df = sum(1 for toks in _DOC_TOKENS if term in toks)
    return math.log(1 + (_N - df + 0.5) / (df + 0.5))


def _bm25_score(
    query_terms: list[str],
    doc_tokens: list[str],
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """BM25 relevance score for a single document against query terms."""
    if not doc_tokens:
        return 0.0
    dl = len(doc_tokens)
    score = 0.0
    for term in set(query_terms):
        tf = doc_tokens.count(term)
        if tf == 0:
            continue
        idf = _idf(term)
        denom = tf + k1 * (1 - b + b * dl / (_AVGDL or 1))
        score += idf * (tf * (k1 + 1)) / (denom or 1)
    return score


# --------------------------------------------------------------------------- #
# MCP tool
# --------------------------------------------------------------------------- #
@mcp.tool()
def search_knowledge_base(query: str, k: int = 3) -> str:
    """Search the station knowledge base and return the top-k relevant passages.

    Use this to answer questions about station facilities, tickets, refunds,
    delay compensation, bicycles, pets, and onboard services. Always cite the
    returned `source` id for any fact you use.

    Args:
        query: The user's question or keywords to search for.
        k: How many passages to return (default 3).

    Returns:
        The top passages, each prefixed with its citable [source] id, or a note
        that nothing relevant was found.
    """
    query_terms = _tokenize(query)
    scored = [
        (_bm25_score(query_terms, _DOC_TOKENS[i]), _PASSAGES[i])
        for i in range(len(_PASSAGES))
    ]
    # Keep only passages with a positive score
    scored = [pair for pair in scored if pair[0] > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = scored[: max(1, k)]

    if not top:
        return "NO_RESULTS: nothing in the knowledge base matched that query."

    blocks = []
    for score, passage in top:
        blocks.append(
            f"[source: {passage['source']} | score: {score:.2f}]\n{passage['text']}"
        )
    return "\n\n---\n\n".join(blocks)


# --------------------------------------------------------------------------- #
# Entry point — stdio transport
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    mcp.run()
