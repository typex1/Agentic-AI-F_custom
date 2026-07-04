# Task 6 — RAG over a Google OKF Knowledge Base

## Goal

Build a document-RAG agent whose knowledge base is a **Google OKF (Open
Knowledge Format)** bundle — a directory of plain markdown files with YAML
frontmatter. The agent must retrieve the most relevant passages from the bundle
and answer **grounded** in them, **citing** the source concept.

This mirrors demo `08_RAG_OKF.py`: same shape (retrieve → ground → cite), but
you assemble the corpus and wire the OKF reader yourself.

Builds on demo `08_RAG_1.py` (structured RAG / self-correcting retrieval) and
`08_RAG_OKF.py` (unstructured RAG over an OKF bundle).

## Background

**OKF** (Open Knowledge Format) is an open, vendor-neutral way to represent
knowledge as a directory of markdown files, each starting with a YAML
frontmatter block (`---` delimited) followed by a free-form body. The only
*required* frontmatter field is `type`; `title`, `description`, `tags`,
`resource`, and `timestamp` are recommended. A concept's **ID** is its file
path within the bundle with `.md` removed. See the spec:
<https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf> →
`SPEC.md`.

Because OKF is "just markdown + frontmatter," any tool or human can produce it,
and any consumer (an LLM, a search index, this agent) can read it verbatim.
That makes it a clean, portable substrate for a RAG knowledge base.

> **No embedding model here.** We only have `bedrock-runtime:Converse` on Nova
> Lite — there is *no* embedding model available (Titan Embeddings, etc. are not
> permitted), and no Bedrock Knowledge Base. So do **lexical retrieval**
> (keyword / TF-IDF / BM25-style scoring) rather than vector search. That is a
> real, valid RAG retriever — only the *ranking* method differs. Call out this
> limitation in your write-up.

### ⚠️ Providing the raw files: upload, don't download

Your knowledge base needs source content. A natural demo corpus is a set of
**YouTube video transcripts** (as in `08_RAG_OKF.py`, which uses transcripts of
Matt Pocock videos). **However, you must supply the raw files by uploading them
yourself** — do **not** try to fetch them from the running instance:

- Downloading YouTube media/transcripts from an **EC2 instance is usually
  blocked** — YouTube rate-limits / blocks data-center IP ranges, and tools like
  `yt-dlp` typically fail with bot / "sign in to confirm you're not a robot"
  errors from cloud hosts. It may also run against YouTube's Terms of Service.
- So do the fetching **on your own machine** (or obtain transcripts you already
  have the rights to), then **upload the files into your bundle directory**
  (e.g. drag them into `solutions/6-rag-okf/OKF_data/` in the IDE, or `scp`
  them up). The `08_RAG_OKF.py` corpus in [`../OKF_data/`](../OKF_data/) was
  prepared exactly this way — prepared elsewhere, uploaded here.
- The corpus does **not** have to be video transcripts. Any small set of text
  documents you can legitimately upload works: your own notes, public docs you
  have rights to, product FAQs, etc. The point is the **OKF format + RAG**, not
  the specific source.

Whatever you pick: keep it small (a handful of files), and make sure each file
is a valid OKF concept (a frontmatter block with a non-empty `type`).

## What you build

1. **An OKF knowledge bundle** — a directory of markdown files, each with a YAML
   frontmatter block (at minimum `type:`, plus `title`/`description`/`tags` as
   useful) and a markdown body. **You upload the raw content** (see the warning
   above); don't scrape it from the instance.
2. **An OKF reader** that walks the bundle, parses frontmatter + body, skips the
   reserved filenames (`index.md`, `log.md`), and computes each concept's ID
   from its path.
3. **A lexical retriever** over the parsed concepts (chunk the bodies; score by
   keyword overlap, TF-IDF, or BM25), returning top-k passages **with their
   source concept ids**.
4. **A RAG agent** that exposes the retriever as tool(s) — e.g.
   `list_knowledge_base`, `search_bundle(query, k)`, `get_concept(id)` — answers
   **only** from retrieved passages, **cites** the source concept, and admits
   when the answer isn't in the bundle.

## Suggested structure

```
solutions/6-rag-okf/             # reference lives here; put your work alongside
  OKF_data/                      # your uploaded OKF bundle (markdown + frontmatter)
    <doc-1>.md
    <doc-2>.md
    ...
  rag_okf.py                     # OKF reader + lexical retriever + RAG agent
```

## Functional requirements

- The agent uses **only** Nova Lite (`amazon.nova-lite-v1:0`) in `us-east-1`.
- The corpus is a valid **OKF bundle**: every non-reserved `.md` file has a
  parseable YAML frontmatter block with a non-empty `type` field.
- The raw files are **uploaded**, not downloaded on the instance.
- Retrieval is **lexical** (no embedding model) and returns passages **with
  source identifiers** (concept ids / video ids).
- The agent **cites** which concept each fact came from.
- For a question **not** covered by the bundle, the agent says it doesn't know
  rather than hallucinating.

## Hints

- Parse frontmatter with `import yaml` and a small regex that splits the leading
  `---`-delimited block from the body. Tolerate files without frontmatter rather
  than crashing.
- Concept ID = path within the bundle, `.md` removed (SPEC §2). Skip `index.md`
  and `log.md` (SPEC §3.1) so they aren't indexed as concepts.
- Derive a `title` from `frontmatter.title`, else the first `# ` heading, else
  the filename; derive a short `description` from a summary section or the first
  paragraph.
- Chunk each body into small overlapping windows (e.g. ~150–200 words) so a hit
  points at something specific to cite. Score with TF-IDF cosine or BM25 — both
  are a few lines and dependency-free.
- Give the agent a `list_knowledge_base` tool that synthesizes an OKF-style
  index (SPEC §6) for progressive disclosure, plus a `get_concept`/`get_document`
  tool to fetch a full concept after a search hit.
- Make the system prompt insist on grounding: "Answer only from retrieved
  passages; cite the source concept; if the answer isn't there, say so."
- See `08_RAG_OKF.py` for a complete, working reference of all of the above.

## Acceptance criteria

- [ ] The bundle is a conformant OKF directory (frontmatter + `type` on every
      concept), assembled from **uploaded** files.
- [ ] The OKF reader parses all concepts and correctly skips reserved filenames.
- [ ] The retriever returns top-k passages **with source ids** using lexical
      scoring (no embedding model).
- [ ] An in-bundle question is answered correctly **with a citation**.
- [ ] An out-of-bundle question yields an honest "not in the knowledge base."

## Stretch goals (optional)

- Generate a spec-conformant bundle-root `index.md` (SPEC §6), including the
  `okf_version: "0.1"` frontmatter that §11 permits only there.
- Upgrade the retriever from keyword-overlap to **BM25** and compare answer
  quality on the same questions.
- Add a CLI (single question / interactive REPL / demo set), like
  `08_RAG_OKF.py`.
- Serve the OKF retriever from your own **MCP server** (combine with Task 3):
  expose `search_bundle` as an MCP tool and consume it via `MCPClient`.
- Compare this OKF document-RAG with demo 08's NL2SQL "structured RAG": when is
  each the right tool?

## Reflection questions

1. What makes OKF a good substrate for a RAG knowledge base compared with, say,
   a proprietary metadata store or a bespoke JSON schema?
2. You used lexical retrieval because no embedding model was available. Where
   would keyword scoring fail that vector search would handle, and vice-versa?
3. Why is downloading source content (e.g. YouTube transcripts) on an EC2
   instance unreliable, and what does uploading-instead change about how you'd
   productionize the ingestion pipeline?
4. How does citing the source concept change the trust model of the agent's
   answers, and how does the OKF concept-id make citation natural?
