from strands import Agent
from strands.models import BedrockModel

# Adjusted: use amazon.nova-lite-v1:0 (only permitted model) in us-east-1
agent = Agent(model=BedrockModel(model_id="amazon.nova-lite-v1:0", region_name="us-east-1"))
agent("Explain what an AI agent is in two sentences.")
