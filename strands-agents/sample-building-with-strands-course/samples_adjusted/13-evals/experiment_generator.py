"""
Automated experiment generation — bootstrap test cases from tool descriptions.
Demonstrates: ExperimentGenerator for creating evaluation suites automatically.
"""

import asyncio
from strands_evals.generators import ExperimentGenerator
from strands_evals.evaluators import TrajectoryEvaluator


# Define what your agent can do
tool_context = """
Available tools:
- lookup_customer(customer_id: str) -> str: Look up customer information by ID
- get_order_history(customer_id: str) -> str: Get order history for a customer
- process_refund(order_id: str, amount: float) -> str: Process a refund for an order

The agent is a customer service assistant for an online electronics store.
It helps customers with order inquiries, refunds, and account questions.
"""


async def generate_experiment():
    # Adjusted: use amazon.nova-lite-v1:0 (only permitted model); the default
    # generator model (claude sonnet) is not accessible in this environment.
    generator = ExperimentGenerator[str, str](str, str, model="amazon.nova-lite-v1:0")

    # Adjusted: the generator's internal structured-output model is named "_Case".
    # Nova Lite drops the leading underscore when emitting the tool call, so the
    # framework never matches it. Renaming the model fixes structured output.
    generator._Case.__name__ = "GeneratedCase"

    experiment = await generator.from_context_async(
        context=tool_context,
        num_cases=5,
        evaluator=TrajectoryEvaluator,
        task_description="Customer service agent handling order and refund requests",
        num_topics=3,
    )

    # Save generated experiment for review
    experiment.to_file("generated_customer_service_eval")
    print("Generated experiment saved!")
    print(f"Cases generated: {len(experiment.cases)}")

    for case in experiment.cases:
        print(f"  - {case.name}: {case.input[:60]}...")

    return experiment


if __name__ == "__main__":
    asyncio.run(generate_experiment())
