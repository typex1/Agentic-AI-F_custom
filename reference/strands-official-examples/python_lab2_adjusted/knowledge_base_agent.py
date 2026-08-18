#!/usr/bin/env python3
"""
# Knowledge Base Agent (adjusted)

This example demonstrates a Strands agent that answers questions from an
Amazon Bedrock Knowledge Base containing corporate compliance / sustainability
documents (ISO certifications, environmental goals, information security).

A small classifier agent first determines the user's intent:
- RETRIEVE: relevant KB content is automatically injected into the model input
  via MemoryManager, and the agent answers from it in a single call.
- STORE: the agent explains that this KB is accessed read-only (see below);
  nothing is written.

## Adjustments for this environment
- All agents run on amazon.nova-lite-v1:0 (the only permitted Bedrock model).
- Uses the current memory API (MemoryManager + BedrockKnowledgeBaseStore)
  instead of the deprecated `memory` tool. Retrieval is handled by automatic
  memory injection: relevant KB content is folded into the model input, so no
  separate retrieve-then-summarize step (or `use_llm` call) is needed.
- The Knowledge Base lives in another AWS account. The store receives an
  injected bedrock-agent-runtime client built from a named credential profile
  (default "xacct", override with STRANDS_KB_PROFILE), while model invocations
  use this instance's own credentials.
- `knowledge_base_type` is set explicitly because the cross-account role lacks
  bedrock:GetKnowledgeBase, which the store would otherwise call to detect it.
- The store path is unavailable: the KB's data source is S3-backed, and writing
  would additionally require s3:PutObject on the owning account's bucket, which
  the cross-account role does not grant. Store requests get an honest message.

## Prerequisites
- ~/.aws/credentials contains a profile (default name "xacct") with
  cross-account access to the KB.
- STRANDS_KNOWLEDGE_BASE_ID env var (defaults to the lab KB below).

## Example Queries

(The lab KB contains corporate compliance / sustainability documents.)

- "What ISO certifications are mentioned?"
- "What are the environmental goals?"
- "Remember that our next audit is on July 25" (reports the read-only limitation)
"""

import os

import boto3
from strands import Agent
from strands.memory import MemoryManager
from strands.vended_memory_stores.bedrock_knowledge_base import BedrockKnowledgeBaseStore

# Adjusted: this environment only permits the amazon.nova-lite-v1:0 Bedrock model.
MODEL_ID = "amazon.nova-lite-v1:0"

# Cross-account KB configuration.
KB_ID = os.environ.get("STRANDS_KNOWLEDGE_BASE_ID", "Y3S3SAL74D")
KB_REGION = os.environ.get("STRANDS_KB_REGION", "us-east-1")
KB_PROFILE = os.environ.get("STRANDS_KB_PROFILE", "xacct")

print(f"Using Knowledge Base ID: {KB_ID} (region {KB_REGION}, credentials profile '{KB_PROFILE}')")

# KB calls run on the cross-account profile via an injected client;
# everything else (model invocation) stays on the default credential chain.
kb_session = boto3.Session(profile_name=KB_PROFILE, region_name=KB_REGION)

knowledge_store = BedrockKnowledgeBaseStore(
    config={
        "knowledge_base_id": KB_ID,
        "knowledge_base_type": "VECTOR",  # skip GetKnowledgeBase detection (not permitted cross-account)
        "data_source_type": "S3",
        "runtime_client": kb_session.client("bedrock-agent-runtime"),
    },
    name="knowledge_base",
    writable=False,  # S3-backed data source; no write permissions via this access path
)

# System prompt to determine the user's intent. Store requests are still
# classified (and then answered with the read-only message below), so the
# examples cover both intents in this KB's domain: corporate compliance /
# sustainability documents.
ACTION_SYSTEM_PROMPT = """
You are a knowledge base assistant focusing ONLY on classifying user queries.
Your task is to determine whether a user query requires STORING information to a knowledge base
or RETRIEVING information from a knowledge base.

Reply with EXACTLY ONE WORD - either "store" or "retrieve".
DO NOT include any explanations or other text.

Examples:
- "What ISO certifications are mentioned?" -> "retrieve"
- "Remember that our next audit is on July 25" -> "store"
- "What are the environmental goals?" -> "retrieve"
- "Add a note that ISO 27001 was renewed this year" -> "store"
- "Which topics does the information security policy cover?" -> "retrieve"
- "Save this: the sustainability report is due in Q3" -> "store"

Only respond with "store" or "retrieve" - no explanation, prefix, or any other text.
"""

ANSWER_SYSTEM_PROMPT = """
You are a helpful assistant that answers questions about corporate compliance
and sustainability documents (ISO certifications, environmental goals,
information security policies). Relevant knowledge base content is injected
into your context automatically; base your answers on it.

Your responses should:
1. Be direct and to the point
2. Not mention document IDs, scores, or other metadata
3. Be conversational but brief
4. Acknowledge when the injected content does not cover the question,
   or when information is conflicting or missing
"""


def determine_action(query):
    """Determine if the query is a store or retrieve action."""
    classifier = Agent(model=MODEL_ID, system_prompt=ACTION_SYSTEM_PROMPT, callback_handler=None)
    action_text = str(classifier(f"Query: {query}")).lower().strip()

    # Default to retrieve if response isn't clear
    return "store" if "store" in action_text else "retrieve"


def run_kb_agent(query):
    """Process a user query with the knowledge base agent."""
    action = determine_action(query)

    if action == "store":
        print(
            "\nI can't store new information: this knowledge base is accessed "
            "read-only (S3-backed data source in another account)."
        )
    else:
        # MemoryManager injects relevant KB content into the model input
        # automatically — retrieval and answering happen in one agent call.
        agent = Agent(
            model=MODEL_ID,
            system_prompt=ANSWER_SYSTEM_PROMPT,
            memory_manager=MemoryManager(stores=[knowledge_store]),
        )
        agent(query)


if __name__ == "__main__":
    # Print welcome message
    print("\n🧠 Knowledge Base Agent 🧠\n")
    print("This agent answers questions from your knowledge base.")
    print("The lab KB contains corporate compliance / sustainability documents. Try:")
    print("- \"What ISO certifications are mentioned?\"")
    print("- \"What are the environmental goals?\"")
    print("\nType your request below or 'exit' to quit:")

    # Interactive loop
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye! 👋")
                break

            if not user_input.strip():
                continue

            # Process the input through the knowledge base agent
            print("Processing...")
            run_kb_agent(user_input)

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
