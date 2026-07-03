"""
Model_permissions.py

Tests various Amazon Bedrock Runtime API actions using boto3 to discover
which permissions are available in the current IAM role.

Actions tested:
  1. Converse (bedrock-runtime:Converse)
  2. ConverseStream (bedrock-runtime:ConverseStream)
  3. InvokeModel (bedrock-runtime:InvokeModel)
  4. InvokeModelWithResponseStream (bedrock-runtime:InvokeModelWithResponseStream)

Additionally tests Bedrock control-plane actions:
  5. ListFoundationModels (bedrock:ListFoundationModels)
  6. GetFoundationModel (bedrock:GetFoundationModel)
"""

import boto3
import json

region = "us-east-1"
model_id = "amazon.nova-lite-v1:0"

bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)
bedrock_client = boto3.client("bedrock", region_name=region)

print("=" * 60)
print("Testing Bedrock API permissions with model:", model_id)
print("=" * 60)

# --- Test 1: Converse ---
print("\n[1] Testing bedrock-runtime:Converse")
try:
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [{"text": "Say hello in one word."}]
            }
        ],
        inferenceConfig={"maxTokens": 10, "temperature": 0.0}
    )
    output_text = response["output"]["message"]["content"][0]["text"]
    print(f"  ✓ ALLOWED - Response: {output_text}")
except Exception as e:
    print(f"  ✗ DENIED or ERROR - {type(e).__name__}: {e}")

# --- Test 2: ConverseStream ---
print("\n[2] Testing bedrock-runtime:ConverseStream")
try:
    response = bedrock_runtime.converse_stream(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [{"text": "Say hi in one word."}]
            }
        ],
        inferenceConfig={"maxTokens": 10, "temperature": 0.0}
    )
    # Consume the stream
    full_text = ""
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            full_text += delta.get("text", "")
    print(f"  ✓ ALLOWED - Response: {full_text}")
except Exception as e:
    print(f"  ✗ DENIED or ERROR - {type(e).__name__}: {e}")

# --- Test 3: InvokeModel ---
print("\n[3] Testing bedrock-runtime:InvokeModel")
try:
    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Say hey in one word."}]
            }
        ],
        "inferenceConfig": {"max_new_tokens": 10, "temperature": 0.0}
    })
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body
    )
    result = json.loads(response["body"].read())
    output_text = result.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", str(result))
    print(f"  ✓ ALLOWED - Response: {output_text}")
except Exception as e:
    print(f"  ✗ DENIED or ERROR - {type(e).__name__}: {e}")

# --- Test 4: InvokeModelWithResponseStream ---
print("\n[4] Testing bedrock-runtime:InvokeModelWithResponseStream")
try:
    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Say yo in one word."}]
            }
        ],
        "inferenceConfig": {"max_new_tokens": 10, "temperature": 0.0}
    })
    response = bedrock_runtime.invoke_model_with_response_stream(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body
    )
    full_text = ""
    for event in response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if "contentBlockDelta" in chunk:
            full_text += chunk["contentBlockDelta"].get("delta", {}).get("text", "")
    print(f"  ✓ ALLOWED - Response: {full_text}")
except Exception as e:
    print(f"  ✗ DENIED or ERROR - {type(e).__name__}: {e}")

# --- Test 5: ListFoundationModels ---
print("\n[5] Testing bedrock:ListFoundationModels")
try:
    response = bedrock_client.list_foundation_models(
        byProvider="Amazon"
    )
    model_count = len(response.get("modelSummaries", []))
    print(f"  ✓ ALLOWED - Found {model_count} Amazon foundation models")
except Exception as e:
    print(f"  ✗ DENIED or ERROR - {type(e).__name__}: {e}")

# --- Test 6: GetFoundationModel ---
print("\n[6] Testing bedrock:GetFoundationModel")
try:
    response = bedrock_client.get_foundation_model(
        modelIdentifier="amazon.nova-lite-v1:0"
    )
    model_name = response["modelDetails"]["modelName"]
    print(f"  ✓ ALLOWED - Model name: {model_name}")
except Exception as e:
    print(f"  ✗ DENIED or ERROR - {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Summary of IAM actions tested:")
print("  bedrock-runtime:Converse")
print("  bedrock-runtime:ConverseStream")
print("  bedrock-runtime:InvokeModel")
print("  bedrock-runtime:InvokeModelWithResponseStream")
print("  bedrock:ListFoundationModels")
print("  bedrock:GetFoundationModel")
print("=" * 60)
