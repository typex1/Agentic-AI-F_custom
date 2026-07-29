# Task 3 — Reference Solution: RAG over a Knowledge Base via Your Own MCP Server

Reference for [`../../tasks/3-rag-and-mcp.md`](../../tasks/3-rag-and-mcp.md).
Compare against this *after* attempting the task.

## Files

| Path | Role |
|------|------|
| `knowledge_base/*.md` | The corpus: `facilities.md`, `tickets.md`, `onboard.md`. |
| `kb_mcp_server.py` | A thin **MCP server** (stdio) that indexes the corpus and exposes `search_knowledge_base(query, k)` with BM25-style lexical ranking. |
| `rag_agent.py` | Connects to the server with `MCPClient`, discovers the tool, and answers **grounded + cited** questions on Nova Lite. |

## Run

```bash
cd strands-agents/solutions/3-rag-and-mcp
python rag_agent.py        # launches kb_mcp_server.py as a subprocess automatically
# (optional) sanity-check retrieval without the agent:
python -c "import kb_mcp_server as k; print(len(k._PASSAGES), 'passages')"
```

## What it demonstrates

- **RAG** — the two phases: *retrieve* (top-k passages) then *generate* (an answer
  grounded strictly in them). The system prompt forbids outside knowledge and
  requires a citation for every fact.
- **Build-your-own MCP** — the retriever lives behind an MCP boundary in a
  separate process, launched over stdio and consumed via `MCPClient` exactly like
  the remote server in demo 04 — but this one is ours.
- **Honest refusal** — for an out-of-corpus question the agent says it doesn't
  know rather than hallucinating.

## Verified behaviour (Nova Lite)

```
"ICE 90 min late compensation?"  -> 25%   (source: tickets.md#Delay compensation)
"large dog conditions?"          -> half fare, muzzle+leash (source: onboard.md#Pets)
"store luggage / how to pay?"    -> lockers, contactless only (source: facilities.md#Luggage)
"last train Cologne->Paris?"     -> "not in the knowledge base"  (correct refusal)
```

## Why lexical retrieval (not vectors)

This environment has **no embedding model** — only `bedrock-runtime:Converse` on
Nova Lite. So retrieval uses **BM25-style keyword scoring** over passages chunked
by `## ` heading (each tagged `file.md#Heading` for citation). The RAG *pattern*
is identical to a vector-store setup; only the ranking method changes. Swapping in
embeddings later would only touch the retriever inside `kb_mcp_server.py` — the
MCP boundary and the agent stay the same. That decoupling is a big part of the
point.

## Notes

- MCP tools are only usable **inside** the `with client:` block; the stdio
  subprocess is torn down when it exits.
- The server's `INFO ... CallToolRequest` lines come from the subprocess (stderr)
  and are a handy visual confirmation that the agent is really calling the MCP
  tool.

## Prerequisites

- `pip install -r ../../../requirements.txt` (the `mcp` client ships with
  `strands-agents`).
- AWS credentials with `bedrock-runtime` access to Nova Lite in `us-east-1`.
