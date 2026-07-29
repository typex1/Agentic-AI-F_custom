# Bedrock Direct (Raw Model Call)

**Python file:** [`../00_bedrock_direct.py`](../00_bedrock_direct.py)

## Learning objective
See what talking to a foundation model looks like *without* any framework: a
raw boto3 call to Amazon Bedrock — prompt in, text out. No agent loop, no
tools, no reasoning steps.

## Why it matters
Every agent in this collection ultimately rests on this one API call. Knowing
what the raw layer looks like makes it obvious what Strands actually adds:
the loop, tool orchestration, message handling, and response parsing you'd
otherwise write yourself.

## What this example demonstrates
- `invoke_model`: the provider-specific action — you build Nova's native
  request body by hand and parse the raw JSON response yourself.
- `converse`: the provider-agnostic unified action — one request/response
  schema across all Bedrock chat models, structured dicts in and out.
- Reading token usage directly from the raw responses.
- Why `converse` is the ergonomic choice for chat/agents — it's exactly the
  action the Strands Agent uses under the hood.

## Key concepts
`boto3` `bedrock-runtime` client, `invoke_model` vs `converse`,
provider-specific vs unified request schemas, token usage — and, by contrast,
everything an `Agent` will handle for us from `01_basic_agent.py` onward.
