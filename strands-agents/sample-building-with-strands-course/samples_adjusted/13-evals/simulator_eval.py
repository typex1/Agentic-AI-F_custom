from strands_evals import Case, Experiment, ActorSimulator
from strands_evals.evaluators import HelpfulnessEvaluator, GoalSuccessRateEvaluator
from strands_evals.mappers import StrandsInMemorySessionMapper
from strands_evals.telemetry import StrandsEvalsTelemetry

from create_agent import create_customer_service_agent

# ---------------------------------------------------------------------------
# Adjusted: ActorSimulator._generate_profile_from_case creates a default Agent()
# (claude sonnet), which is not accessible in this environment. Patch it to use
# amazon.nova-lite-v1:0 (the only permitted model).
# ---------------------------------------------------------------------------
from strands import Agent
from strands.models import BedrockModel
from strands_evals.simulation.profiles.actor_profile import DEFAULT_USER_PROFILE_SCHEMA
from strands_evals.simulation.prompt_templates.actor_profile_extraction import ACTOR_PROFILE_PROMPT_TEMPLATE
from strands_evals.types.simulation.actor import ActorProfile

MODEL = BedrockModel(model_id="amazon.nova-lite-v1:0", region_name="us-east-1")


def _generate_profile_from_case_nova(case: Case) -> ActorProfile:
    initial_query = case.input
    task_description = case.metadata.get("task_description", "") if case.metadata else ""
    profile_prompt = ACTOR_PROFILE_PROMPT_TEMPLATE.format(
        initial_query=initial_query,
        task_description=task_description,
        example=DEFAULT_USER_PROFILE_SCHEMA,
    )
    profile_agent = Agent(model=MODEL, callback_handler=None)
    result = profile_agent(profile_prompt, structured_output_model=ActorProfile)
    return result.structured_output


ActorSimulator._generate_profile_from_case = staticmethod(_generate_profile_from_case_nova)

# Setup telemetry for trace-based evaluation
telemetry = StrandsEvalsTelemetry().setup_in_memory_exporter()
memory_exporter = telemetry.in_memory_exporter


def task_function(case: Case) -> dict:
    """Run a multi-turn simulated conversation with the full customer service agent."""

    # Create simulator to drive the conversation
    # Adjusted: simulator LLM uses nova-lite (only permitted model)
    simulator = ActorSimulator.from_case_for_user_simulator(
        case=case,
        model="amazon.nova-lite-v1:0",
        max_turns=8,
    )

    # Create the full customer service agent (tools, steering, skills)
    agent = create_customer_service_agent(
        trace_attributes={
            "gen_ai.conversation.id": case.session_id,
            "session.id": case.session_id,
        },
        callback_handler=None,
    )

    # Run multi-turn conversation
    user_message = case.input

    while simulator.has_next():
        agent_response = agent(user_message)
        user_result = simulator.act(str(agent_response))
        user_message = str(user_result.structured_output.message)

    # Map traces to session for evaluation
    all_spans = memory_exporter.get_finished_spans()
    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(all_spans, session_id=case.session_id)

    return {"output": str(agent_response), "trajectory": session}


# Define test cases with goals the simulator will try to achieve
test_cases = [
    Case[str, str](
        name="refund-request",
        input="Hi, I need to return a laptop I bought. My customer ID is C-1001.",
        metadata={"task_description": "Customer gets refund processed for their order"},
    ),
    Case[str, str](
        name="order-tracking",
        input="Can you check on my orders? My customer ID is C-1002.",
        metadata={"task_description": "Customer receives order status information"},
    ),
    Case[str, str](
        name="account-issue",
        input="My account seems to be having issues. Customer ID C-1001.",
        metadata={"task_description": "Customer gets account troubleshooting help"},
    ),
]

# Evaluate with multiple evaluators
# Adjusted: LLM judges use nova-lite (default judge model is not accessible)
evaluators = [
    HelpfulnessEvaluator(model="amazon.nova-lite-v1:0"),
    GoalSuccessRateEvaluator(model="amazon.nova-lite-v1:0"),
]

experiment = Experiment[str, str](cases=test_cases, evaluators=evaluators)
# Adjusted: run_evaluations returns a single EvaluationReport in strands-evals 1.0.1
report = experiment.run_evaluations(task_function)

print("=== Multi-Turn Simulation Results ===")
report.run_display()
