"""
07_RAG_OKF.py — Unstructured RAG Agent over a Google OKF knowledge base

A companion to `07_RAG_1.py`. Where that sample does *structured* RAG (it
retrieves a database schema and turns natural language into SQL), this file
does *unstructured* RAG: it retrieves relevant passages from a corpus of
markdown documents and grounds the model's answers in them.

The corpus is a **Google OKF (Open Knowledge Format) knowledge bundle**:
    https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf

OKF is a deliberately minimal, vendor-neutral format: a directory of UTF-8
markdown files, each beginning with a YAML frontmatter block delimited by
`---`, followed by a free-form markdown body (see okf/SPEC.md v0.1). The only
*required* frontmatter field is `type`; `title`, `description`, `resource`,
`tags` and `timestamp` are recommended. A concept's ID is its file path within
the bundle with the `.md` suffix removed.

THE KNOWLEDGE BASE (demonstration corpus)
-----------------------------------------
`strands-agents/OKF_data/` holds ten OKF concept documents — the transcripts of
the ten latest videos from the "Matt Pocock" YouTube channel
(https://www.youtube.com/@mattpocockuk/videos). Each file's frontmatter looks
like:

    ---
    type: video_transcript
    video_id: dtAJ2dOd3ko
    publish_date: 2026-05-21
    tags: [ai-agents, skills, context-management, handoff, claude-code]
    ---
    # /handoff is my new favourite skill
    ## Quick Summary
    ...
    ## Full transcript
    ...

The YouTube video id is also embedded at the end of each filename, so a concept
maps cleanly back to its source video (https://youtu.be/<video_id>). The
transcripts were prepared and provided out-of-band — this script only *reads*
the local bundle; it never contacts YouTube.

ADAPTATIONS FOR THIS LIMITED-PERMISSION ENVIRONMENT
---------------------------------------------------
As in `07_RAG_1.py`, we only have `bedrock-runtime:Converse` on
`amazon.nova-lite-v1:0` (see .kiro/steering/Permissions.md). That constrains
two design choices:

  * Model     → amazon.nova-lite-v1:0  (the only model we may call)
  * Retrieval → local, dependency-free lexical search (TF-IDF cosine)
                instead of a hosted vector store or Bedrock Knowledge Base.
                Embedding models (e.g. Titan) would need InvokeModel on a model
                other than Nova Lite, which is not permitted here, and a Bedrock
                Knowledge Base needs bedrock-agent-runtime:Retrieve, which we
                also lack. Lexical search keeps the RAG loop faithful — retrieve,
                ground, answer — with zero extra permissions or dependencies.

The retrieval "index" is built in-process from the OKF bundle on first use, so
no external setup is required. This file is fully self-contained and runnable
from any working directory.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import os
import re
import math
import logging
from pathlib import Path
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import yaml

from strands import Agent, tool
from strands.models import BedrockModel

logging.getLogger("strands").setLevel(logging.WARNING)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = "amazon.nova-lite-v1:0"  # Only model available with our permissions

# The OKF knowledge bundle lives alongside this script.
BUNDLE_DIR = Path(__file__).resolve().parent / "OKF_data"

# Reserved OKF filenames that are never concept documents (SPEC.md §3.1).
OKF_RESERVED_FILENAMES = {"index.md", "log.md"}

# Chunking parameters for retrieval (words, not tokens — good enough for lexical
# search and keeps chunks small enough to fit several into Nova Lite's context).
CHUNK_WORDS = 180
CHUNK_OVERLAP_WORDS = 40


# --------------------------------------------------------------------------- #
# OKF bundle parsing
# --------------------------------------------------------------------------- #
@dataclass
class Concept:
    """One parsed OKF concept document."""

    concept_id: str            # file path within bundle, sans ".md" (SPEC §2)
    path: Path
    frontmatter: Dict[str, Any]
    body: str
    title: str
    description: str

    @property
    def type(self) -> str:
        return str(self.frontmatter.get("type", "unknown"))

    @property
    def video_id(self) -> Optional[str]:
        vid = self.frontmatter.get("video_id")
        return str(vid) if vid is not None else None

    @property
    def tags(self) -> List[str]:
        tags = self.frontmatter.get("tags", [])
        return [str(t) for t in tags] if isinstance(tags, list) else []

    @property
    def source_url(self) -> Optional[str]:
        """Best-effort link back to the underlying resource."""
        if self.frontmatter.get("resource"):
            return str(self.frontmatter["resource"])
        if self.video_id:
            return f"https://youtu.be/{self.video_id}"
        return None


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def _split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Split an OKF markdown file into (frontmatter_dict, body).

    Per SPEC §4, frontmatter is a YAML block delimited by `---` lines at the
    very start of the file. Files without a leading frontmatter block are
    tolerated (returned with empty frontmatter) rather than rejected.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text.strip()
    raw_fm, body = match.group(1), match.group(2)
    try:
        data = yaml.safe_load(raw_fm) or {}
        if not isinstance(data, dict):
            data = {}
    except yaml.YAMLError:
        data = {}
    return data, body.strip()


def _derive_title(frontmatter: Dict[str, Any], body: str, path: Path) -> str:
    """Title priority: frontmatter.title -> first H1 heading -> filename."""
    if frontmatter.get("title"):
        return str(frontmatter["title"])
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem


def _derive_description(frontmatter: Dict[str, Any], body: str) -> str:
    """Description priority: frontmatter.description -> first sentence of the
    '## Quick Summary' section -> first non-heading paragraph."""
    if frontmatter.get("description"):
        return str(frontmatter["description"])

    lines = body.splitlines()
    # Look for a "Quick Summary" (or any) section and take its first paragraph.
    summary_lines: List[str] = []
    in_summary = False
    for line in lines:
        if line.strip().lower().startswith("## quick summary"):
            in_summary = True
            continue
        if in_summary:
            if line.strip().startswith("#"):
                break
            if line.strip():
                summary_lines.append(line.strip())
            elif summary_lines:
                break
    paragraph = " ".join(summary_lines).strip()

    if not paragraph:
        # Fall back to the first non-heading, non-empty paragraph in the body.
        for line in lines:
            if line.strip() and not line.strip().startswith("#"):
                paragraph = line.strip()
                break

    # Trim to the first sentence for a compact index description.
    if paragraph:
        first_sentence = re.split(r"(?<=[.!?])\s", paragraph, maxsplit=1)[0]
        return first_sentence.strip()
    return ""


@lru_cache(maxsize=1)
def load_bundle() -> Tuple[Concept, ...]:
    """Load and parse every concept document in the OKF bundle.

    Reserved filenames (index.md, log.md) are skipped per SPEC §3.1. Results
    are cached so the bundle is parsed only once per process.
    """
    if not BUNDLE_DIR.exists():
        raise FileNotFoundError(f"OKF bundle directory not found: {BUNDLE_DIR}")

    concepts: List[Concept] = []
    for md_path in sorted(BUNDLE_DIR.rglob("*.md")):
        if md_path.name in OKF_RESERVED_FILENAMES:
            continue
        text = md_path.read_text(encoding="utf-8")
        frontmatter, body = _split_frontmatter(text)
        concept_id = md_path.relative_to(BUNDLE_DIR).with_suffix("").as_posix()
        concepts.append(
            Concept(
                concept_id=concept_id,
                path=md_path,
                frontmatter=frontmatter,
                body=body,
                title=_derive_title(frontmatter, body, md_path),
                description=_derive_description(frontmatter, body),
            )
        )
    if not concepts:
        raise FileNotFoundError(f"No OKF concept documents found in {BUNDLE_DIR}")
    return tuple(concepts)


# --------------------------------------------------------------------------- #
# OKF index.md generation (SPEC §6 progressive disclosure)
# --------------------------------------------------------------------------- #
OKF_VERSION = "0.1"


def render_index_md() -> str:
    """Render a spec-conformant bundle-root ``index.md`` for the OKF bundle.

    Per SPEC §6, an index enumerates the directory's contents as a bulleted
    list of ``[Title](relative-url) - description`` entries grouped under
    headings. Index files normally carry no frontmatter, but §11 permits a
    single ``okf_version`` declaration in the *bundle-root* index — which is
    exactly what this is — so we include it.
    """
    concepts = load_bundle()
    lines = [
        "---",
        f'okf_version: "{OKF_VERSION}"',
        "---",
        "",
        "# Video Transcripts",
        "",
        (
            "Transcripts of the ten latest videos from the Matt Pocock YouTube "
            "channel (https://www.youtube.com/@mattpocockuk/videos), stored as "
            "OKF `video_transcript` concepts. Each entry links to the concept "
            "document; the YouTube video id is embedded in the filename and "
            "frontmatter."
        ),
        "",
    ]
    # Sort newest-first by publish_date when available, else by title.
    def _sort_key(c: "Concept"):
        return (str(c.frontmatter.get("publish_date", "")), c.title)

    for c in sorted(concepts, key=_sort_key, reverse=True):
        rel_url = c.path.relative_to(BUNDLE_DIR).as_posix()
        publish = c.frontmatter.get("publish_date", "?")
        desc = c.description or "(no description)"
        lines.append(f"* [{c.title}]({rel_url}) - {desc} (published {publish})")
    lines.append("")
    return "\n".join(lines)


def write_index_md() -> Path:
    """Write the generated ``index.md`` to the bundle root and return its path."""
    index_path = BUNDLE_DIR / "index.md"
    index_path.write_text(render_index_md(), encoding="utf-8")
    return index_path


# --------------------------------------------------------------------------- #
# Lexical retrieval index (TF-IDF cosine over document chunks)
# --------------------------------------------------------------------------- #
# A tiny, well-known English stopword list keeps common words from dominating
# the similarity score. Deliberately small — no external NLP dependency.
_STOPWORDS = frozenset(
    """
    a an and are as at be but by for from has have he her his i if in into is it
    its of on or she that the their them then there these they this to was were
    what when where which who will with you your yours we our us not no do does
    did done can could would should about so up out down over under just like
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


@dataclass
class Chunk:
    """A retrievable passage drawn from a concept's body."""

    concept_id: str
    title: str
    video_id: Optional[str]
    text: str
    tf: Dict[str, int] = field(default_factory=dict)


def _chunk_words(words: List[str]) -> List[List[str]]:
    """Split a word list into overlapping windows."""
    if len(words) <= CHUNK_WORDS:
        return [words] if words else []
    step = CHUNK_WORDS - CHUNK_OVERLAP_WORDS
    chunks = []
    for start in range(0, len(words), step):
        window = words[start : start + CHUNK_WORDS]
        if window:
            chunks.append(window)
        if start + CHUNK_WORDS >= len(words):
            break
    return chunks


@dataclass
class RetrievalIndex:
    chunks: List[Chunk]
    idf: Dict[str, float]

    def _tfidf_vector(self, tf: Dict[str, int]) -> Dict[str, float]:
        # Sublinear tf weighting (1 + log tf) scaled by idf.
        return {
            term: (1.0 + math.log(count)) * self.idf.get(term, 0.0)
            for term, count in tf.items()
            if self.idf.get(term, 0.0) > 0.0
        }

    def search(self, query: str, top_k: int = 4) -> List[Tuple[Chunk, float]]:
        q_terms = _tokenize(query)
        if not q_terms:
            return []
        q_tf: Dict[str, int] = {}
        for t in q_terms:
            q_tf[t] = q_tf.get(t, 0) + 1
        q_vec = self._tfidf_vector(q_tf)
        if not q_vec:
            return []
        q_norm = math.sqrt(sum(w * w for w in q_vec.values()))

        scored: List[Tuple[Chunk, float]] = []
        for chunk in self.chunks:
            c_vec = self._tfidf_vector(chunk.tf)
            if not c_vec:
                continue
            dot = sum(q_vec[t] * c_vec.get(t, 0.0) for t in q_vec)
            if dot <= 0.0:
                continue
            c_norm = math.sqrt(sum(w * w for w in c_vec.values()))
            score = dot / (q_norm * c_norm) if q_norm and c_norm else 0.0
            if score > 0.0:
                scored.append((chunk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


@lru_cache(maxsize=1)
def build_index() -> RetrievalIndex:
    """Build the in-process TF-IDF retrieval index from the OKF bundle."""
    chunks: List[Chunk] = []
    for concept in load_bundle():
        words = concept.body.split()
        for window in _chunk_words(words):
            text = " ".join(window)
            tf: Dict[str, int] = {}
            for token in _tokenize(text):
                tf[token] = tf.get(token, 0) + 1
            if tf:
                chunks.append(
                    Chunk(
                        concept_id=concept.concept_id,
                        title=concept.title,
                        video_id=concept.video_id,
                        text=text,
                        tf=tf,
                    )
                )

    # Document frequency across chunks -> inverse document frequency.
    n_docs = len(chunks)
    df: Dict[str, int] = {}
    for chunk in chunks:
        for term in chunk.tf:
            df[term] = df.get(term, 0) + 1
    idf = {term: math.log((n_docs + 1) / (freq + 1)) + 1.0 for term, freq in df.items()}
    return RetrievalIndex(chunks=chunks, idf=idf)


# --------------------------------------------------------------------------- #
# Tools (the "retrieval" surface the agent calls)
# --------------------------------------------------------------------------- #
@tool
def list_knowledge_base() -> str:
    """List every concept in the OKF knowledge base (progressive disclosure).

    This synthesizes an OKF-style index (SPEC §6) on the fly: one line per
    concept with its title, concept id, source video id, tags and a one-line
    description. Call this first to see what topics are available before
    searching or opening a full transcript.

    Returns:
        A markdown listing of all concepts in the bundle.
    """
    lines = ["# OKF Knowledge Base — video_transcript concepts\n"]
    for c in load_bundle():
        publish = c.frontmatter.get("publish_date", "?")
        tags = ", ".join(c.tags) if c.tags else "—"
        lines.append(
            f"* **{c.title}**\n"
            f"  - concept_id: `{c.concept_id}`\n"
            f"  - video_id: `{c.video_id}`  (published {publish})\n"
            f"  - tags: {tags}\n"
            f"  - {c.description}"
        )
    return "\n".join(lines)


@tool
def search_transcripts(query: str, top_k: int = 4) -> str:
    """Retrieve the passages most relevant to a query from the OKF bundle.

    This is the core RAG retrieval step. It runs a local TF-IDF cosine search
    over chunked transcript text and returns the best-matching passages, each
    tagged with its source concept so answers can be grounded and cited.

    Args:
        query: Natural-language search query (keywords or a question).
        top_k: Maximum number of passages to return (default 4).

    Returns:
        Formatted passages with relevance scores and source concept ids, or a
        message if nothing relevant was found.
    """
    top_k = max(1, min(int(top_k), 8))
    results = build_index().search(query, top_k=top_k)
    if not results:
        return (
            f"No relevant passages found for: {query!r}. "
            "Try different keywords or call list_knowledge_base to see topics."
        )

    out = [f"Top {len(results)} passages for: {query!r}\n"]
    for i, (chunk, score) in enumerate(results, start=1):
        out.append(
            f"[{i}] score={score:.3f}  from \"{chunk.title}\" "
            f"(concept_id: {chunk.concept_id}, video_id: {chunk.video_id})\n"
            f"{chunk.text}\n"
        )
    return "\n".join(out)


@tool
def get_transcript(identifier: str) -> str:
    """Fetch a full concept document from the OKF bundle.

    Use this after search_transcripts when you need the complete transcript
    for a specific video rather than a short passage.

    Args:
        identifier: A concept_id (e.g. "handoff_is_my_new_favourite_skill_dtAJ2dOd3ko"),
            a video_id (e.g. "dtAJ2dOd3ko"), or a case-insensitive substring of
            the title.

    Returns:
        The concept's frontmatter and body, or a not-found message.
    """
    ident = identifier.strip()
    ident_low = ident.lower()
    concepts = load_bundle()

    match = None
    for c in concepts:
        if c.concept_id == ident or c.video_id == ident:
            match = c
            break
    if match is None:  # fall back to fuzzy title / concept_id match
        for c in concepts:
            if ident_low in c.title.lower() or ident_low in c.concept_id.lower():
                match = c
                break

    if match is None:
        available = ", ".join(c.video_id or c.concept_id for c in concepts)
        return f"No concept matched {identifier!r}. Available video_ids: {available}"

    fm = yaml.safe_dump(match.frontmatter, sort_keys=False, allow_unicode=True).strip()
    source = f"\nSource: {match.source_url}" if match.source_url else ""
    return f"concept_id: {match.concept_id}{source}\n\n---\n{fm}\n---\n\n{match.body}"


# --------------------------------------------------------------------------- #
# Agent factory
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """
You are a knowledge assistant that answers questions about a library of YouTube
video transcripts stored as a Google OKF (Open Knowledge Format) knowledge base.
The videos are from Matt Pocock's channel and focus on AI coding agents, skills,
and workflows.

Follow this retrieval-augmented generation (RAG) process:
1. If you are unsure what topics exist, call list_knowledge_base first.
2. Call search_transcripts with focused keywords from the user's question to
   retrieve the most relevant passages.
3. If a passage is promising but you need fuller context, call get_transcript
   for that concept_id or video_id.
4. Answer ONLY using information found in the retrieved passages. Do not rely on
   outside knowledge or invent details.
5. If the knowledge base does not contain the answer, say so plainly.

When you answer:
- Be concise and specific.
- Cite the source video(s) you used by their title and video_id, e.g.
  (source: "/handoff is my new favourite skill", video_id dtAJ2dOd3ko).
- If multiple videos are relevant, synthesize across them.
"""


def create_okf_rag_agent() -> Agent:
    """Create the unstructured RAG agent grounded in the OKF bundle."""
    model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.0)
    return Agent(
        model=model,
        tools=[list_knowledge_base, search_transcripts, get_transcript],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )


# --------------------------------------------------------------------------- #
# CLI / Demo
# --------------------------------------------------------------------------- #
def _print_header() -> None:
    print("=== OKF RAG Agent (video-transcript knowledge base, Nova Lite) ===")
    print(f"Bundle: {BUNDLE_DIR}")
    print(f"Concepts loaded: {len(load_bundle())}  |  Chunks indexed: {len(build_index().chunks)}\n")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Ask questions against the OKF video-transcript knowledge base.",
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="Question to ask. If omitted, runs the built-in demo questions "
        "(or starts an interactive session with --interactive).",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Start an interactive prompt; type questions until you enter "
        "'exit', 'quit', or an empty line.",
    )
    args = parser.parse_args()

    agent = create_okf_rag_agent()
    _print_header()

    # 1) Single question passed on the command line.
    if args.question:
        question = " ".join(args.question)
        print(f"Q: {question}")
        print(f"A: {agent(question)}")
        return

    # 2) Interactive REPL (one agent instance -> conversation keeps context).
    if args.interactive:
        print("Interactive mode. Ask a question (empty line, 'exit' or 'quit' to stop).\n")
        while True:
            try:
                question = input("Q: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not question or question.lower() in {"exit", "quit"}:
                break
            print(f"A: {agent(question)}\n")
        return

    # 3) Default: run the built-in demo questions.
    questions = [
        "What is the handoff skill and why is it useful?",
        "Why does Matt say large context windows have a 'dumb zone'?",
        "What does the triage skill help with?",
        "According to these videos, how should you deal with AI-generated 'slop' in a codebase?",
    ]
    for q in questions:
        print(f"Q: {q}")
        print(f"A: {agent(q)}\n")
        print("-" * 70)


if __name__ == "__main__":
    main()
