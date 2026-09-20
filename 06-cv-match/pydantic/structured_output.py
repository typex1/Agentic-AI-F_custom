"""Strands structured output example.

This script DOES call an LLM: `agent(...)` sends the prompt to the model
(via Amazon Bedrock) and Strands returns a validated PersonInfo object.

For the pure pydantic version with no LLM involved, see pydantic_only.py.
"""

from pydantic import BaseModel, Field
from strands import Agent

# 1) Define the Pydantic model
class PersonInfo(BaseModel):
    """Model that contains information about a Person"""
    name: str = Field(description="Name of the person")
    age: int = Field(description="Age of the person")
    occupation: str = Field(description="Occupation of the person")

# 2) Pass the model to the agent
agent = Agent(
    model="amazon.nova-lite-v1:0"
)

# Spec: https://strandsagents.com/docs/api/python/strands.agent.agent/
result = agent(
    "John Smith is a 30 year-old software engineer",
    structured_output_model=PersonInfo
)

# 3) Access the `structured_output` from the result
person_info: PersonInfo = result.structured_output
print(f"Name: {person_info.name}")      # "John Smith"
print(f"Age: {person_info.age}")        # 30
print(f"Job: {person_info.occupation}") # "software engineer"
