"""
Custom deterministic evaluator — no LLM judge needed.
Demonstrates: Building pure Python evaluators for fast, free assertions.
"""

from strands import Agent
from strands.models import BedrockModel
from strands_evals import eval_task, Case, Experiment
from strands_evals.evaluators import Evaluator
from strands_evals.types import EvaluationData, EvaluationOutput

# Adjusted: use amazon.nova-lite-v1:0 (only permitted model) in us-east-1
MODEL = BedrockModel(model_id="amazon.nova-lite-v1:0", region_name="us-east-1")


class ResponseLengthEvaluator(Evaluator[str, str]):
    """Evaluates that responses fall within an acceptable length range."""

    def __init__(self, min_words: int = 10, max_words: int = 200):
        # Adjusted: base Evaluator requires super().__init__() in strands-evals 1.0.1
        super().__init__()
        self.min_words = min_words
        self.max_words = max_words

    def evaluate(self, evaluation_case: EvaluationData[str, str]) -> EvaluationOutput:
        response = evaluation_case.actual_output
        word_count = len(response.split())

        if self.min_words <= word_count <= self.max_words:
            return EvaluationOutput(
                score=1.0,
                test_pass=True,
                reason=f"Response length ({word_count} words) is within acceptable range [{self.min_words}-{self.max_words}]",
                label="appropriate_length",
            )
        elif word_count < self.min_words:
            return EvaluationOutput(
                score=0.0,
                test_pass=False,
                reason=f"Response too short ({word_count} words, minimum is {self.min_words})",
                label="too_short",
            )
        else:
            return EvaluationOutput(
                score=0.5,
                test_pass=False,
                reason=f"Response too long ({word_count} words, maximum is {self.max_words})",
                label="too_long",
            )


@eval_task()
def get_response():
    return Agent(
        model=MODEL,
        system_prompt="You are a concise assistant. Answer questions in 1-3 sentences.",
        callback_handler=None,
    )


test_cases = [
    Case[str, str](
        name="concise-answer",
        input="What is Python?",
        metadata={"category": "conciseness"},
    ),
    Case[str, str](
        name="detailed-answer",
        input="Explain the entire history of computing from 1940 to present day.",
        metadata={"category": "conciseness"},
    ),
]

# Deterministic evaluator — fast, free, no LLM calls
evaluator = ResponseLengthEvaluator(min_words=10, max_words=100)

experiment = Experiment[str, str](cases=test_cases, evaluators=[evaluator])
# Adjusted: run_evaluations returns a single EvaluationReport in strands-evals 1.0.1
report = experiment.run_evaluations(get_response)

print("=== Custom Deterministic Evaluator Results ===")
report.run_display()
