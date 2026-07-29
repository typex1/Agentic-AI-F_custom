# Structured Output

**Python file:** [`../04_structured_output.py`](../04_structured_output.py)

## Learning objective
Get typed, validated data out of an agent instead of free-form text you have to
parse.

## Why it matters
Real applications need reliable data structures, not prose. Structured output
lets you plug an agent directly into downstream code, APIs, or databases with
type safety and validation guarantees.

## What this example demonstrates
- Defining output schemas as Pydantic `BaseModel`s (`BookRecommendation`,
  `MovieAnalysis`) with field descriptions and constraints.
- Requesting typed output with `structured_output_model=...`.
- Accessing validated, typed fields via `result.structured_output`.

## Key concepts
Pydantic `BaseModel`/`Field`, `structured_output_model`, schema-constrained
generation, `result.structured_output`.
