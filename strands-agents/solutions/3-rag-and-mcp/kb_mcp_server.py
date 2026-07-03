"""
kb_mcp_server.py — a thin MCP server exposing a knowledge-base search tool

Part of the Task 3 reference solution. This is a *separate process*: the RAG
agent (rag_agent.py) launches it over stdio via MCPClient and calls the tool it
exposes.

Retrieval is LEXICAL (BM25-style), not vector-based, because this environment has
no embedding model — only `bedrock-runtime:Converse` on Nova Lite. The RAG
*pattern* (retrieve passages -> ground the answer -> cite sources) is unchanged;
only the ranking method differs from a vector store.

The corpus lives in ./knowledge_base/*.md and is chunked into passages by
`## ` heading, each tagged with a citable source id like "facilities.md#Luggage".

Run standalone (for a manual check) with:  python kb_mcp_server.py
(but normally the agent starts it as a subprocess).
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

KB_DIR = Path(__file__).resolve().parent / "knowledge_base"

mcp = FastMCP("station-knowledge-base")


# --------------------------------------------------------------------------- #
# Corpus loading + chunking
# --------------------------------------------------------------------------- #
def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _load_passages() -> list[dict]:
    """Chunk every .md file into passages split on '## ' headings.

    Each passage: {"source": "<file>#<heading>", "text": "<heading + body>"}.
    """
    passages: list[dict] = []
    for md in sorted(KB_DIR.glob("*.md")):
        raw = md.read_text(encoding="utf-8")
        # Split on level-2 headings, keeping the heading with its body.
        chunks = re.split(r"\n(?=## )", raw)
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk or chunk.startswith("# ") and "\n" not in chunk:
                continue
            heading_match = re.search(r"##\s+(.+)", chunk)
            heading = heading_match.group(1).strip() if heading_match else md.stem
            passages.append({"source": f"{md.name}#{heading}", "text": chunk})
    return passages


_PASSAGES = _load_passages()

# Precompute IDF for BM25-style scoring.
_DOC_TOKENS = [_tokenize(p["text"]) for p in _PASSAGES]
_N = max(len(_PASSAGES), 1)
_AVGDL = (sum(len(t) for t in _DOC_TOKENS) / _N) if _PASSAGES else 0.0


def _idf(term: str) -> float:
    df = sum(1 for toks in _DOC_TOKENS if term in toks)
    # BM25 idf with +1 smoothing to stay non-negative.
    return math.log(1 + (_N - df + 0.5) / (df + 0.5))


def _bm25_score(query_terms: list[str], doc_tokens: list[str], k1: float = 1.5, b: float = 0.75) -> float:
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
# The MCP tool
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
    scored = [pair for pair in scored if pair[0] > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = scored[: max(1, k)]

    if not top:
        return "NO_RESULTS: nothing in the knowledge base matched that query."

    blocks = []
    for score, passage in top:
        blocks.append(f"[source: {passage['source']} | score: {score:.2f}]\n{passage['text']}")
    return "\n\n---\n\n".join(blocks)


if __name__ == "__main__":
    # stdio transport: the client (rag_agent.py) speaks MCP over stdin/stdout.
    mcp.run()
