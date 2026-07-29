"""
00_bedrock_direct.py — Raw Bedrock model call (no agent yet)

Demonstrates the two lowest-level ways to talk to a foundation model on
Amazon Bedrock, both via boto3 and with no agent loop, no tools, and no
reasoning steps — just prompt in, text out:

  1. `invoke_model`  — the raw, provider-specific call.
  2. `converse`      — the newer, provider-agnostic unified call.

This is the starting point. Everything after this (01_basic_agent.py onward)
builds on top of this same underlying call:

    Raw model call (this file)
        → Agent wraps the model + a loop  (01_basic_agent.py)
            → Agent + tools                (02_custom_tools.py)
                → Multi-agent, RAG, MCP... (later demos)

Permissions note: this environment only permits `bedrock-runtime` actions on
`amazon.nova-lite-v1:0` in us-east-1. `invoke_model` is one of the allowed
runtime actions, so this works without any Bedrock control-plane access.
"""

import json
import boto3

MODEL_ID = "amazon.nova-lite-v1:0"
REGION = "us-east-1"

# A bedrock-runtime client is all we need — no control-plane calls.
client = boto3.client("bedrock-runtime", region_name=REGION)

# Nova's native request schema: messages + inference configuration.
# (Each provider on Bedrock has its own body format; this is Nova's.)

# ---------------------------------------------------------------------------
# Section 1 — The `invoke_model` action
# ---------------------------------------------------------------------------


prompt = "What are the three laws of robotics?"

body = {
    "messages": [
        {"role": "user", "content": [{"text": prompt}]},
    ],
    "inferenceConfig": {
        "maxTokens": 512,
        "temperature": 0.7,
    },
}

# The single API call. `invoke_model` sends the raw body and returns raw bytes.
response = client.invoke_model(
    modelId=MODEL_ID,
    body=json.dumps(body),
)

# The response body is a stream of JSON bytes we decode ourselves.
result = json.loads(response["body"].read())

# Nova returns the assistant turn under output.message.content[].text
text = result["output"]["message"]["content"][0]["text"]

print("=== Raw invoke_model Response ===")
print(text)

# Token usage is reported in the response too — no metrics object like an agent,
# just the raw numbers.
usage = result.get("usage", {})
print("\n=== Usage ===")
print(f"Input tokens:  {usage.get('inputTokens')}")
print(f"Output tokens: {usage.get('outputTokens')}")

# Notice what's missing compared to an Agent: we hand-built the request body,
# parsed the raw response, and there was no reasoning/tool loop. The Strands
# Agent (next file) handles all of that for us.


# ---------------------------------------------------------------------------
# Section 2 — The `converse` action
# ---------------------------------------------------------------------------
#
# `invoke_model` vs `converse` — what's the difference?
#
#   invoke_model:
#     - Provider-specific. YOU build the request body in each model's own
#       native schema (Nova, Claude, Llama, Titan... all differ) and YOU
#       parse the model's own native response shape.
#     - Body is opaque JSON that you serialize/deserialize by hand.
#     - Switching models often means rewriting the body and parsing code.
#
#   converse:
#     - Provider-agnostic. Bedrock exposes ONE unified request/response
#       schema across all chat models. The same code works whether the
#       modelId is Nova, Claude, or Llama — Bedrock translates internally.
#     - Structured Python dicts in, structured dict out — no manual
#       json.dumps / json.loads of an opaque body.
#     - System prompts, multi-turn messages, tool use, and inference config
#       are first-class, uniform fields.
#
# Both are `bedrock-runtime` actions and both are permitted here. `converse`
# is the recommended path for chat-style models, and it's exactly what the
# Strands Agent uses under the hood.

# Same client, same model — just a different action.
converse_response = client.converse(
    modelId=MODEL_ID,
    messages=[
        {"role": "user", "content": [{"text": prompt}]},
    ],
    inferenceConfig={
        "maxTokens": 512,
        "temperature": 0.7,
    },
)

# Unified response shape (identical regardless of provider): the assistant
# turn lives under output.message.content[].text — already a Python dict,
# no manual JSON decoding needed.
converse_text = converse_response["output"]["message"]["content"][0]["text"]

print("\n=== converse Response ===")
print(converse_text)

# Usage is reported in a normalized `usage` field, with the same keys for
# every model.
converse_usage = converse_response.get("usage", {})
print("\n=== Usage (converse) ===")
print(f"Input tokens:  {converse_usage.get('inputTokens')}")
print(f"Output tokens: {converse_usage.get('outputTokens')}")

# Takeaway: converse gives you portability (one schema for all models) while
# invoke_model gives you full access to a model's raw, native API. For agents
# and chat, converse is the ergonomic choice — which is why the frameworks
# in the later demos build on it.
