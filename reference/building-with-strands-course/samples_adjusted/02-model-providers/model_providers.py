from strands import Agent
from strands.models import BedrockModel
# Adjusted: optional provider packages (anthropic/openai/ollama extras) are not installed
# from strands.models.anthropic import AnthropicModel
# from strands.models.ollama import OllamaModel
# from strands.models.openai import OpenAIModel
import os

# Adjusted: Bedrock with amazon.nova-lite-v1:0 (only permitted model) in us-east-1
bedrock_model = BedrockModel(
    model_id="amazon.nova-lite-v1:0",
    region_name="us-east-1",
)

# anthropic_model = AnthropicModel(
#     client_args={"api_key": os.environ["ANTHROPIC_API_KEY"]},
#     model_id="claude-sonnet-4-20250514",
#     max_tokens=1024,
#     params={"temperature": 0.7},
# )


# openai_model = OpenAIModel(
#     client_args={"api_key": os.environ["OPENAI_API_KEY"]},
#     model_id="gpt-4o",
#     params={"max_tokens": 1000, "temperature": 0.7},
# )

# Adjusted: Ollama requires a local server (not available in this environment)
# ollama_model = OllamaModel(
#     host="http://localhost:11434",
#     model_id="gemma4:latest",
# )

agent = Agent(model=bedrock_model)
agent("Explain the agent loop in one paragraph.")
