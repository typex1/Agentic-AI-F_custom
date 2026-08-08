from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.executors import SequentialToolExecutor


@tool
def step_one() -> str:
    """Perform the first step of the workflow."""
    return "Step one complete — file created."


@tool
def step_two() -> str:
    """Perform the second step that depends on step one."""
    return "Step two complete — file processed."


agent = Agent(
    # Adjusted: use amazon.nova-lite-v1:0 (only permitted model) in us-east-1
    model=BedrockModel(model_id="amazon.nova-lite-v1:0", region_name="us-east-1"),
    tools=[step_one, step_two],
    tool_executor=SequentialToolExecutor(),
)
agent("Run step one and then step two.")
