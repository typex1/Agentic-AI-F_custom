# 08 — Unstructured RAG over a Google OKF knowledge base

**Python file:** [`../08_RAG_OKF.py`](../08_RAG_OKF.py)

## Learning objective
Build a retrieval-augmented agent that answers questions from a corpus of
markdown documents — a Google **OKF (Open Knowledge Format)** knowledge bundle —
by retrieving the most relevant passages and grounding its answers in them.

OKF Bundle file structure:
```
my-knowledge-bundle/           ◄── The "Bundle" (a standard folder)
├── index.md                    ◄── Reserved: Root index (lists what's available)
├── log.md                      ◄── Reserved: Chronological history of changes
│
├── playbooks/                  ◄── Folder organizing a specific category
│   ├── deployment-guide.md     ◄── Concept File (Markdown + YAML frontmatter)
│   └── troubleshooting.md      ◄── Concept File 
│
└── data-assets/                
    ├── customer_metrics.md     ◄── Concept File
    └── index.md                ◄── Sub-directory Index (for progressive disclosure)
```

Anatomy of an OKF Concept .md file:
```
---
type: TableData                 ◄── [CRITICAL] The only strictly required field
title: Customer Core Metrics
description: Main table containing aggregated ARR and churn metrics.
resource: bigquery://project.dataset.customer_metrics
tags: [finance, sales]
timestamp: 2026-07-05T12:00:00Z
---

# Customer Core Metrics

This section contains the free-form human-readable description. Because it's 
standard markdown, I can link to another concept file in the bundle like this:
See our [Troubleshooting Playbook](../playbooks/troubleshooting.md) for data mismatches.
```

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

## How the context window is protected

Even with many `.md` files — and some of them very large (full video
transcripts) — the model's context window is never exhausted. Several layers
work together:

1. **Chunking keeps passages small.**
   Every document body is split into overlapping windows of ~180 words
   (`CHUNK_WORDS = 180`, `CHUNK_OVERLAP_WORDS = 40`). A 10,000-word transcript
   becomes ~60 chunks, but the model never sees the whole file unless
   explicitly asked.

2. **TF-IDF retrieval returns only `top_k` chunks (default 4, max 8).**
   Regardless of how many documents or chunks exist in the index, only the 4–8
   best-matching passages (~720–1440 words total) are injected into the prompt
   per `search_transcripts` call. The index itself lives in Python memory, not
   in the LLM context.

3. **`list_knowledge_base` returns metadata, not content.**
   It shows title, concept_id, video_id, tags, and a one-sentence description
   per document — never the body text. This is the OKF "progressive disclosure"
   pattern (SPEC §6): show the catalogue first, drill down only when needed.

4. **The system prompt enforces a staged workflow.**
   The agent is instructed to search first (getting small chunks), and only call
   `get_transcript` (which *does* return a full body) when it really needs
   deeper context for a specific document — one document at a time, so it stays
   bounded.

In short: the entire corpus is never loaded into the prompt. Only small,
relevant slices are sent to the model, selected by a retrieval step that runs
entirely in Python.

## No OKF library — and that's the point

There is no `import okf` in the script. The entire OKF parsing is hand-rolled
(~60 lines): `yaml.safe_load` for frontmatter, `pathlib` for file discovery, a
regex for the `---` delimiters, and the `Concept` dataclass to hold the result.

This is intentional. OKF is a *spec/convention*, not a software library. The
format is deliberately minimal — UTF-8 markdown files with YAML frontmatter in a
directory — so that any tool or agent can produce and consume it without a
dedicated SDK. The script's `_split_frontmatter()`, `load_bundle()`, and
`Concept` *are* the "OKF library" here, purpose-built inline to show how little
code the format requires.
