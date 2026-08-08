"""
Basic output evaluation using LLM-as-a-judge.
Demonstrates: Cases, Evaluators, Experiments, and the @eval_task decorator.
"""

from strands import Agent
from strands.models import BedrockModel
from strands_evals import eval_task, Case, Experiment
from strands_evals.evaluators import OutputEvaluator

# Adjusted: use amazon.nova-lite-v1:0 (only permitted model) in us-east-1
MODEL = BedrockModel(model_id="amazon.nova-lite-v1:0", region_name="us-east-1")


# The @eval_task decorator handles boilerplate — just return an Agent
@eval_task()
def get_response():
    return Agent(
        model=MODEL,
        system_prompt="You are a helpful assistant that provides accurate, concise information.",
        callback_handler=None,
    )


# Define test cases
test_cases = [
    Case[str, str](
        name="factual-knowledge",
        input="What is the capital of France?",
        expected_output="The capital of France is Paris.",
        metadata={"category": "knowledge"},
    ),
    Case[str, str](
        name="math-reasoning",
        input="What is 15% of 200?",
        expected_output="30",
        metadata={"category": "math"},
    ),
    Case[str, str](
        name="explanation",
        input="Explain what an API is in one sentence.",
        expected_output="An API is an interface that allows different software systems to communicate with each other.",
        metadata={"category": "explanation"},
    ),
]

# Define evaluator with a custom rubric
evaluator = OutputEvaluator(
    # Adjusted: LLM judge also uses nova-lite (default judge model is not accessible)
    model=MODEL,
    rubric="""
    Evaluate the response based on:
    1. Accuracy - Is the information factually correct?
    2. Completeness - Does it fully answer the question?
    3. Clarity - Is it easy to understand?

    Score 1.0 if all criteria are met excellently.
    Score 0.5 if some criteria are partially met.
    Score 0.0 if the response is inadequate or incorrect.
    """,
    include_inputs=True,
)

# Create and run experiment
experiment = Experiment[str, str](cases=test_cases, evaluators=[evaluator])
# Adjusted: run_evaluations returns a single EvaluationReport in strands-evals 1.0.1
report = experiment.run_evaluations(get_response)

# Display results
print("=== Basic Output Evaluation Results ===")
report.run_display()
