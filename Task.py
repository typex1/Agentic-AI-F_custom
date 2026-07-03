print("Task 2.1: Environment setup")
# Install the Strands Agents framework and tools
# %pip install strands-agents strands-agents-tools

print("Task 2.2: Create your first AI agent")
import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow") 

from strands import Agent

# Create your first AI agent
agent = Agent(callback_handler=None,
    model="amazon.nova-lite-v1:0",
    system_prompt="You are a helpful assistant that provides concise responses."
)

# Send a message to the agent
response = agent("Hello! Tell me a joke.")
print(response)

print("Task 2.3: Add tools to your agent")
from strands import Agent, tool
from strands_tools import calculator

# Create a weather tool
@tool
def weather():
    """Get current weather information"""
    return "Sunny and O degree Celsius"

# Create an agent with tools
agent_with_tools = Agent(callback_handler=None,
    model="amazon.nova-lite-v1:0",
    tools=[calculator, weather],
    system_prompt="You are a helpful assistant. You can do math calculations and use the weather tool to tell the weather."
)

# Test the agent with both tools in one query
# Note: This query requires both tools - the weather tool to get temperature in Celsius,
# and the calculator tool to convert from Celsius to Fahrenheit.
# The agent will automatically determine which tools to use and in what order.
response = agent_with_tools("What is the weather in Seattle in Fahrenheit?")
print(response)

# Test with a math question that only needs the calculator tool
# The agent will analyze the question and decide to use only the calculator tool
math_query = "What is 25 * 4 + 18?"
print("=== Agent Chooses Calculator Tool ===")
print(f"Query: {math_query}")
response = agent_with_tools(math_query)
print(f"Response: {response}")

print("Task 2.3: Direct Tool Invocation")
# Call the calculator tool directly
# Note: Direct tool invocation bypasses the agent's conversation flow.
# Use agent_with_tools.tool.calculator() to call the calculator tool directly
# without the agent deciding which tool to use. This is useful for testing
# specific tools or when you know exactly which tool function you need.
result = agent_with_tools.tool.calculator(expression="2 + 3 * 4")
print(f"Calculator result: {result}")

print("Task 2.4: Configure logging")
import logging
from strands import Agent
import os

# Enable detailed logging to understand what the agent is doing
logging.getLogger("strands").setLevel(logging.INFO)

# Set up logging to write to both console and file
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()  # Console output
    ]
)

# Create a logger
logger = logging.getLogger("agent_activity")

# Create an agent with logging enabled
logger.info("Creating new agent with Nova Lite model")
logged_agent = Agent(callback_handler=None,model="amazon.nova-lite-v1:0")

logger.info("Sending message to agent: 'Hello! How are you?'")
response = logged_agent("Hello! How are you?")
print(response)

print("Task 2.5: Explore model configuration")
from strands import Agent
from strands.models import BedrockModel

# Create a custom model configuration
custom_model = BedrockModel(
    model_id="amazon.nova-lite-v1:0",
    temperature=0.3  # Lower temperature = more consistent responses
)

# Create an agent with the custom model
custom_agent = Agent(callback_handler=None,model=custom_model)
print("Agent created successfully!")

print("Task 2.6: Build a recipe assistant agent")
# %pip install ddgs

from strands import Agent, tool
from ddgs import DDGS
from ddgs.exceptions import RatelimitException, DDGSException
import logging

# Set up logging
logging.getLogger("strands").setLevel(logging.INFO)

# Create a web search tool
@tool
def websearch(keywords: str, max_results: int = 3) -> str:
    """Search the web for information.
    Args:
        keywords (str): What to search for
        max_results (int): How many results to return
    Returns:
        Search results as text
    """
    try:
        results = DDGS().text(keywords, max_results=max_results)
        return results if results else "No results found."
    except Exception as e:
        return f"Search error: {e}"

print("Web search tool created successfully!")

# Create the recipe assistant agent
recipe_agent = Agent(callback_handler=None,
    model="amazon.nova-lite-v1:0",
    system_prompt="""You are RecipeBot, a helpful cooking assistant.
    Help users find recipes and answer cooking questions.
    Use the websearch tool to find recipes and cooking information.""",
    tools=[websearch]
)

print("Recipe assistant agent created successfully!")

# Test the recipe assistant
response = recipe_agent("Suggest a simple recipe with chicken and broccoli.")
print(response)
