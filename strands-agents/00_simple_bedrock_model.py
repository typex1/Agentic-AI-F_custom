"""
00_simple_bedrock_model.py — Raw Bedrock model call (no agent yet)

Demonstrates the lowest-level way to talk to a foundation model on Amazon
Bedrock: a single `invoke_model` request via boto3. There is no agent loop,
no tools, and no reasoning steps — just prompt in, text out.

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
