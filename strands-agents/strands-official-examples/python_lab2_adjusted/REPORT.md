# Report: Python Examples under the nova-lite-v1 Constraint

Assessment of every example in `site/docs/examples/python/` against this environment's
permissions, which allow **only** the `amazon.nova-lite-v1:0` Bedrock model.
Adjusted, verified copies live in `site/docs/examples/python_adjusted/`.

## Environment

- Python 3.12.13, strands-agents 1.51.0, strands-agents-tools 0.8.6, boto3, mcp (region `us-east-1`)
- `amazon.nova-lite-v1:0` — Converse works ✅
- Default SDK model (`global.anthropic.claude-sonnet-4-6`) — `AccessDeniedException` ❌
- Also denied: `amazon.nova-canvas-v1:0`, `amazon.titan-embed-text-v2:0`, `bedrock-agent:ListKnowledgeBases`

**Key finding:** no example works as-is. The Strands SDK hardcodes Claude Sonnet as the
default model (no environment-variable override exists), so every `Agent()` call needed an
explicit `model="amazon.nova-lite-v1:0"` argument. That is the only change made; all other
logic is untouched.

## Working after adjustment (in `python_adjusted/`)

Each was run end to end with real input (`BYPASS_TOOL_CONSENT=true`, piped stdin):

| Example | Test performed | Result |
|---|---|---|
| `weather_forecaster.py` | "What is the weather like in Seattle?" | ✅ Fetched and summarized NWS forecast via `http_request` |
| `file_operations.py` | Read lines from a test file | ✅ Tools execute correctly (see caveat below) |
| `mcp_calculator.py` | "What is 12 plus 34?" | ✅ Started FastMCP server, called `add` tool, answered 46 |
| `graph_loops_example.py` | `demo` (haiku task) | ✅ Loop executed: writer → checker → writer → checker → finalizer |
| `agents_workflow.py` | Fact-check "Tuesday comes before Monday" | ✅ 3-agent pipeline correctly ruled the claim false |
| `multi_agent_example/` | "What is the square root of 1764?" | ✅ Orchestrator routed to math assistant; calculator returned 42 |

> **Removed by decision:** `meta_tooling.py` worked in testing but only with retries and
> very explicit prompts — nova-lite frequently looped on file creation without producing
> the tool file. Too unreliable for a student-facing lab, so it was removed from this
> folder. The original remains in `python/` for reference.

### Caveats (model quality, not code defects)

- **nova-lite occasionally misreads successful tool results.** In `file_operations.py` it
  sometimes claimed a read failed even though the tool returned the file content (verified
  by inspecting the message history: tool results were correct). Retrying or rephrasing helps.
- Weaker instruction-following overall compared to the Claude models the examples were
  written for; multi-step tasks may need more explicit prompts.

## Not workable under the given constraints (excluded from `python_adjusted/`)

| Example | Blocker |
|---|---|
| `memory_agent.py` | Fails at import: the `mem0` package is not installed. Even if installed, mem0's Bedrock backend requires `amazon.titan-embed-text-v2:0` for embeddings and defaults to `claude-3-5-haiku` as its LLM; both components share one credential chain, so the cross-account split used for `knowledge_base_agent.py` does not carry over. **De-scoped by decision** after cross-account access became available. |
| `multimodal.py` | The `generate_image` tool only supports Stability models (`stability.stable-image-core-v1:1` — invalid/unavailable in this account) and the Amazon alternative `nova-canvas` is AccessDenied. Verified: the tool returns an error even with the agent model overridden to nova-lite. No permitted image-generation model exists. |

## Update: `knowledge_base_agent.py` recovered via cross-account access

Initially non-workable (no Bedrock KB in this account; `bedrock-agent:ListKnowledgeBases`
AccessDenied). A KB in another account (`160817128410`, KB `LFGRFTJTFC`, `us-east-1`)
was later made accessible and the example was adjusted and added to `python_adjusted/`:

- **Credentials:** this instance's role is denied `sts:AssumeRole`, so temporary
  credentials for the cross-account role `KB-role-Lab-2` are installed as the
  `xacct` profile in `~/.aws/credentials` (minted by `xacct_3_mint_temp_creds.py`,
  expire after ≤12 h and must be re-minted).
- **Current memory API:** the original example used the `memory` tool, which is
  deprecated (runtime warning; becomes an error log in strands-agents-tools
  v0.9.0). The adjusted copy uses the documented migration path instead:
  `MemoryManager` + `BedrockKnowledgeBaseStore`. This also simplified the
  cross-account split — the store accepts an injected `bedrock-agent-runtime`
  client built from the `xacct` profile, while model calls stay on the instance
  role. `knowledge_base_type` is set explicitly because the cross-account role
  lacks `bedrock:GetKnowledgeBase` (used for auto-detection).
- **`use_llm` replaced** with a direct `Agent(model=MODEL_ID, ...)` call for query
  classification — `use_llm` spawns nested agents on the SDK default model
  (blocked Claude) with no model parameter. The retrieve-then-summarize step is
  gone entirely: `MemoryManager` injects relevant KB content into the model input
  automatically.
- **Verified end to end:** retrieval questions matching the KB's actual content —
  corporate compliance / sustainability documents ("What ISO certifications are
  mentioned?", "What are the environmental goals?") — answered correctly, with
  zero deprecation warnings.
- **Store path unavailable via this access path:** the KB's only data source is
  S3-backed, so writes go through `s3:PutObject` on the owning account's bucket,
  which the cross-account role does not grant. (The deprecated `memory` tool
  could not write to S3 data sources at all.) The store is configured
  `writable=False` and store requests get an honest read-only message. Full
  store/retrieve needs either a CUSTOM data source or S3 write permissions on
  the bucket added to the role.

## Adjustment pattern

Every adjusted file adds one constant and passes it to each `Agent(...)` call
(16 call sites across 12 files, verified complete and compiling):

```python
# Adjusted: this environment only permits the amazon.nova-lite-v1:0 Bedrock model.
MODEL_ID = "amazon.nova-lite-v1:0"

agent = Agent(model=MODEL_ID, ...)
```
