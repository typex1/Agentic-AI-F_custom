# Strands Official Examples

Python examples from the official Strands Agents repository, plus copies
adjusted to run in this lab environment.

## Source

The `python/` folder is an unmodified copy of the official examples from:

> https://github.com/strands-agents/harness-sdk/tree/main/site/docs/examples/python

## Why two folders?

| Folder | Contents |
|--------|----------|
| `python/` | The original examples, exactly as published upstream. Kept for reference and for diffing against the adjusted versions. |
| `python_lab2_adjusted/` | Adjusted, lab-2-ready copies — every example here has been run end to end and verified working in this environment. |

The original examples assume broad AWS permissions (effectively admin rights).
This lab environment is deliberately restricted: only the `bedrock-runtime`
actions (`Converse`, `ConverseStream`, `InvokeModel`,
`InvokeModelWithResponseStream`) are permitted, and only for the
**`amazon.nova-lite-v1:0`** model in `us-east-1` (see
[`.kiro/steering/Permissions.md`](../../.kiro/steering/Permissions.md)).

Because the Strands SDK hardcodes a Claude model as its default, **no original
example works as-is** — every `Agent()` call needs an explicit
`model="amazon.nova-lite-v1:0"` argument. That is the core adjustment; a few
examples needed more:

- `knowledge_base_agent.py` — rewritten for the current memory API
  (`MemoryManager` + `BedrockKnowledgeBaseStore`) and for cross-account,
  read-only access to the lab Knowledge Base via the `xacct` credential
  profile. Example questions match the KB's actual content (corporate
  compliance / sustainability documents).
- `memory_agent.py` and `multimodal.py` — **not included**: they require
  packages or models (mem0 embeddings, image generation) that are not
  available under this environment's permissions.
- `meta_tooling.py` — **removed by decision**: it works in principle, but
  nova-lite is too unreliable at the required multi-step file creation for a
  student-facing lab.

See [`python_lab2_adjusted/REPORT.md`](python_lab2_adjusted/REPORT.md) for the
full per-example assessment, test transcript summaries, and caveats.

## Running the adjusted examples

```bash
pip install -r ../../requirements.txt   # from the repo root: requirements.txt

cd python_lab2_adjusted
python3 weather_forecaster.py           # each example is an interactive loop; type 'exit' to quit
```

Notes:

- Tools that modify files or run commands ask for consent; set
  `BYPASS_TOOL_CONSENT=true` to skip prompts in non-interactive runs.
- `knowledge_base_agent.py` additionally needs valid (short-lived) `xacct`
  credentials in `~/.aws/credentials` — see the file header for details.
