"""
12_conversation_management.py — Controlling Message History

Adapted from the Strands Agents sample:
  strands-agents/samples → python/01-learn/17-conversation-management

WHAT IT DOES
------------
Conversation managers control how an agent's message history grows and stays
within the model's context window. This demo shows the three built-in
strategies:

  1. SlidingWindowConversationManager (default) — keep the last N messages,
     preserving tool-use/tool-result pairs.
  2. NullConversationManager — do nothing; send full history every time
     (raises on overflow). Useful when you manage context yourself.
  3. SummarizingConversationManager — summarize old messages instead of
     dropping them, preserving context while staying small.

ADAPTATION FOR THIS LIMITED-PERMISSION ENVIRONMENT
--------------------------------------------------
Per .kiro/steering/Permissions.md we only have `bedrock-runtime:Converse` on
`amazon.nova-lite-v1:0`. Conversation management is a client-side concern and
only needs model invocation, so it runs as-is on Nova Lite.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import (
    SlidingWindowConversationManager,
    NullConversationManager,
    SummarizingConversationManager,
)

MODEL_ID = "amazon.nova-lite-v1:0"
AWS_REGION = "us-east-1"


def _model() -> BedrockModel:
    return BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.0)


def _msg_count(agent: Agent) -> int:
    return len(agent.messages)


# --------------------------------------------------------------------------- #
# 1. Sliding window — keep only the last N messages
# --------------------------------------------------------------------------- #
def demo_sliding_window() -> None:
    print("=== 1. SlidingWindowConversationManager ===\n")
    # Small window so we can see trimming happen quickly.
    agent = Agent(
        model=_model(),
        conversation_manager=SlidingWindowConversationManager(window_size=6),
        system_prompt="You are a concise assistant. Answer in one short sentence.",
        callback_handler=None,
    )

    turns = [
        "My name is Dana.",
        "I live in Berlin.",
        "My favorite language is Python.",
        "I have a dog named Pixel.",
        "What is my name?",  # 'Dana' may have been trimmed out of the window
    ]
    for t in turns:
        agent(t)

    print(f"window_size=6 → messages retained after {len(turns)} user turns: "
          f"{_msg_count(agent)}")
    print("(Older messages beyond the window are dropped; tool pairs stay intact.)\n")


# --------------------------------------------------------------------------- #
# 2. Null manager — never trims (full history every call)
# --------------------------------------------------------------------------- #
def demo_null_manager() -> None:
    print("=== 2. NullConversationManager ===\n")
    agent = Agent(
        model=_model(),
        conversation_manager=NullConversationManager(),
        system_prompt="You are a concise assistant. Answer in one short sentence.",
        callback_handler=None,
    )
    for t in ["My name is Dana.", "I live in Berlin.", "What is my name?"]:
        agent(t)

    print(f"NullConversationManager → all messages kept: {_msg_count(agent)}")
    print("(Nothing is dropped; on real overflow it raises ContextWindowOverflowException.)\n")


# --------------------------------------------------------------------------- #
# 3. Summarizing manager — summarize old turns instead of dropping them
# --------------------------------------------------------------------------- #
def demo_summarizing() -> None:
    print("=== 3. SummarizingConversationManager ===\n")
    agent = Agent(
        model=_model(),
        conversation_manager=SummarizingConversationManager(
            summary_ratio=0.5,          # summarize up to 50% of oldest messages
            preserve_recent_messages=2,  # always keep the last 2 verbatim
        ),
        system_prompt="You are a concise assistant. Answer in one short sentence.",
        callback_handler=None,
    )

    facts = [
        "My name is Dana.",
        "I live in Berlin.",
        "My favorite language is Python.",
        "I have a dog named Pixel.",
        "I work as a data engineer.",
        "I am learning to play the cello.",
    ]
    for f in facts:
        agent(f)

    # Ask something from an early turn; summarization should preserve the gist.
    result = agent("Based on our conversation, what is my name and where do I live?")
    print(f"messages retained: {_msg_count(agent)}")
    print(f"Recall after summarization: {result}\n")


def main() -> None:
    demo_sliding_window()
    demo_null_manager()
    demo_summarizing()


if __name__ == "__main__":
    main()
