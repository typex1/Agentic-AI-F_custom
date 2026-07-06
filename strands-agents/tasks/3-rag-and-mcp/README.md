# Task 3 — RAG over a Knowledge Base via MCP Server

## Overview

This solution implements document-based RAG (Retrieval-Augmented Generation)
exposed through a custom MCP server, consumed by a Strands agent.

## Architecture

```
rag_agent.py  ──MCPClient (stdio)──▶  kb_mcp_server.py
                                           │
                                           ▼
                                     knowledge_base/
                                       ├── facilities.md
                                       ├── onboard.md
                                       └── tickets.md
```

1. **kb_mcp_server.py** — A thin MCP server (FastMCP, stdio transport) that:
   - Loads `.md` files from `knowledge_base/` at startup
   - Chunks them by `## ` headings into citable passages
   - Scores queries using BM25 (lexical retrieval, no embedding model needed)
   - Exposes `search_knowledge_base(query, k)` as an MCP tool

2. **rag_agent.py** — A Strands agent that:
   - Launches the MCP server as a subprocess via `MCPClient`
   - Discovers `search_knowledge_base` tool
   - Answers questions grounded in retrieved passages with citations
   - Refuses to answer when the knowledge base doesn't contain the information

## Key design decisions

- **Lexical retrieval (BM25)** — No embedding model is available in this
  environment (only `bedrock-runtime:Converse` on Nova Lite). BM25 is a valid,
  well-established retrieval method; it excels at exact keyword matching but may
  miss semantic paraphrases that vector search handles.

- **MCP boundary** — The retriever runs in a separate process, providing:
  - Process isolation (crashes don't bring down the agent)
  - Reusability across multiple agents
  - Language independence (could be rewritten in any language)
  - Clean separation of concerns

- **Citation requirement** — The system prompt mandates citing `[source: ...]`
  ids, making answers auditable and trustworthy.

## Running

```bash
python rag_agent.py
```

The agent will automatically launch the MCP server subprocess, discover its
tools, and answer the demo questions.

## Model

Amazon Nova Lite (`amazon.nova-lite-v1:0`) via Amazon Bedrock, us-east-1.
