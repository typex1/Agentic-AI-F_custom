# Task 3 — RAG over a Knowledge Base, Served via Your Own MCP Server

## Goal

Two skills in one task, exactly as Module 3 frames them:

1. **RAG** — ground the agent's answers in a **knowledge base** so it stops
   guessing and starts citing.
2. **MCP** — expose that knowledge base as a tool from a **thin MCP server you
   build yourself**, and consume it from a Strands agent.

Putting them together gives the Module 3 picture: *consume a knowledge base via
an MCP server, and build your own thin MCP server.* Your retrieval logic lives
behind a clean MCP boundary; the agent just sees a `search_knowledge_base` tool.

Builds on demos `07_mcp_tools.py` (consuming an MCP server) and `08_RAG_1.py`
(retrieval-augmented answering).

## Background

**RAG** = *retrieve* relevant context, then *generate* an answer grounded in it.
The retrieval step is the interesting part. Demo `08_RAG_1.py` does "structured
RAG" — it retrieves a **database schema** and generates **SQL**. You'll do
document RAG: retrieve the most relevant passages from a small corpus and let the
model answer from them, with citations.

> **No embedding model here.** We only have `bedrock-runtime:Converse` on Nova
> Lite — there is *no* embedding model available (Titan Embeddings, etc. are not
> permitted). So do **lexical retrieval** (keyword / BM25-style scoring) rather
> than vector search. That's a real, valid RAG retriever — only the *ranking*
> method differs from a vector store. Name this limitation explicitly in your
> write-up; it's a good discussion point.

**MCP** (Model Context Protocol) lets an agent use tools hosted by a separate
process. In demo 07 you *consumed* a remote MCP server. Here you'll *build* one:
a small local server (stdio transport) that exposes your retriever as a tool,
then connect to it with `MCPClient`.

## What you build

1. **A knowledge base** — a handful of documents (markdown/text) about your
   domain (e.g. station facilities, travel policies, FAQ). Keep it small.
2. **A thin MCP server** (`kb_mcp_server.py`) that:
   - loads/indexes the corpus at startup,
   - exposes a tool like `search_knowledge_base(query, k)` returning the top-k
     passages **with their source ids** (so answers can cite),
   - runs over **stdio** (launched as a subprocess by the client).
3. **A RAG agent** (`rag_agent.py`) that connects to the server with `MCPClient`,
   discovers its tool, and answers questions **grounded** in retrieved passages,
   **citing** the source of each fact. It must refuse/admit when the answer isn't
   in the knowledge base.

## Suggested structure

```
solutions/3-rag-and-mcp/         # reference lives here; put your work alongside
  knowledge_base/                # the corpus (a few .md files)
  kb_mcp_server.py               # thin MCP server: indexes corpus, serves search
  rag_agent.py                   # MCPClient -> agent, grounded + cited answers
```

## Functional requirements

- The agent uses **only** Nova Lite (`amazon.nova-lite-v1:0`).
- Retrieval is **lexical** (no embedding model) and returns passages **with
  source identifiers**.
- The retriever is exposed as an **MCP tool from your own server** and consumed
  via `MCPClient` (not just an in-process `@tool`).
- The agent **cites** which document each fact came from.
- For a question **not** covered by the corpus, the agent says it doesn't know
  rather than hallucinating.

## Hints

- MCP server: `from mcp.server.fastmcp import FastMCP`, decorate a function with
  `@mcp.tool()`, and run `mcp.run()` (stdio). Client side (see demo 07 for the
  `with`-context pattern):
  ```python
  from mcp import stdio_client, StdioServerParameters
  from strands.tools.mcp import MCPClient
  client = MCPClient(lambda: stdio_client(
      StdioServerParameters(command="python", args=["kb_mcp_server.py"])))
  with client:
      tools = client.list_tools_sync()
      agent = Agent(model=..., tools=tools, system_prompt=...)
  ```
  Everything using MCP tools must stay **inside** the `with` block — the
  connection closes when it exits.
- A simple, dependency-free retriever: tokenise, score each passage by query-term
  overlap (bonus: TF-IDF or BM25 weighting), return the top-k with their doc ids.
- Chunk documents into small passages (e.g. by paragraph or heading) so a hit
  points at something specific to cite.
- Make the system prompt insist on grounding: "Answer only from
  `search_knowledge_base` results; cite the source id; if the answer isn't there,
  say so."
- The MCP server is a separate process — `print()` debugging there goes to its
  stderr, not your agent's stdout.

## Acceptance criteria

- [ ] `kb_mcp_server.py` runs as an MCP server and exposes a working
      `search_knowledge_base` tool.
- [ ] `rag_agent.py` connects via `MCPClient`, discovers the tool, and uses it.
- [ ] An in-corpus question is answered correctly **with a citation**.
- [ ] An out-of-corpus question yields an honest "not in the knowledge base."

## Stretch goals (optional)

- Upgrade the retriever from keyword-overlap to **BM25** and compare answer
  quality on the same questions.
- Add a second MCP tool (e.g. `get_document(doc_id)`) and let the agent fetch a
  full document after finding it via search.
- Return a relevance score with each passage and have the agent prefer
  higher-scoring sources.
- Compare this document-RAG approach with demo 08's NL2SQL "structured RAG":
  when is each the right tool?

## Reflection questions

1. What are the two phases of RAG, and which one did MCP encapsulate here?
2. You used lexical retrieval because no embedding model was available. Where
   would keyword scoring fail that vector search would handle, and vice-versa?
3. What did putting the retriever behind MCP buy you, versus a plain in-process
   `@tool`? (Think: process isolation, reuse across agents, language independence.)
4. How does citing sources change the trust model of the agent's answers?
