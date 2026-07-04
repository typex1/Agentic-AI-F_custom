# 08 — Unstructured RAG over a Google OKF knowledge base

**Python file:** [`../08_RAG_OKF.py`](../08_RAG_OKF.py)

## Learning objective
Build a retrieval-augmented agent that answers questions from a corpus of
markdown documents — a Google **OKF (Open Knowledge Format)** knowledge bundle —
by retrieving the most relevant passages and grounding its answers in them.

## Why it matters
Where `08_RAG_1.py` does *structured* RAG (schema retrieval → SQL), this is the
*unstructured* counterpart that most people mean by "RAG": search a document
corpus, feed the best passages to the model, and answer only from what was
retrieved. It also shows how to consume an open, vendor-neutral knowledge format
(plain markdown + YAML frontmatter) that any tool or agent can produce and read.

## What this example demonstrates
- An **OKF bundle reader**: parses YAML frontmatter + markdown body per the OKF
  v0.1 spec, derives titles/descriptions, and computes concept IDs from file
  paths (reserved `index.md`/`log.md` are skipped).
- The knowledge base is the transcripts of the ten latest Matt Pocock videos,
  stored in [`../OKF_data/`](../OKF_data/) with the YouTube video id in each
  filename and frontmatter.
- **Dependency-free lexical retrieval** (TF-IDF cosine over chunked text) as the
  retrieval step — no vector store, no embedding model, no extra permissions.
- Three retrieval tools: `list_knowledge_base` (synthesizes an OKF index for
  progressive disclosure), `search_transcripts` (core RAG retrieval), and
  `get_transcript` (fetch a full concept by id / video_id / title).
- A generated, spec-conformant bundle-root [`index.md`](../OKF_data/index.md)
  (`render_index_md` / `write_index_md`), including the `okf_version: "0.1"`
  frontmatter §11 permits only there.
- A small `argparse` CLI: single question, `--interactive` REPL, or the built-in
  demo questions.
- Adapting a document-RAG pattern to Nova Lite under this environment's limited
  permissions (no Bedrock Knowledge Base / embedding models).

## Key concepts
Unstructured RAG, Open Knowledge Format (OKF), YAML frontmatter + markdown,
chunking, TF-IDF cosine retrieval, retrieval tools, answer grounding &
citations, progressive disclosure via `index.md`.
