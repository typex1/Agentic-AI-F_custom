# Task: get structured output

Free-text answers are hard to use in code. Make your agent return **typed,
validated data** instead.

1. Define a small Pydantic model `SupportTicket` with fields:
   `customer_name: str`, `topic: str`, `urgency: Literal["low", "medium", "high"]`,
   and `summary: str` (one sentence). Add a `Field(description=...)` to each —
   the descriptions guide the model.
2. Call your agent with `structured_output_model=SupportTicket` on a free-text
   complaint of your choice, e.g.:
   > "Hi, this is Maria. My invoice from last month shows the wrong amount
   > and I need this fixed before Friday!"
3. Print the returned object's fields individually (not as one string) and
   show that `urgency` is guaranteed to be one of the three allowed values.
4. Try an input where a field is ambiguous — what does the model put there?

This technique is the glue of every larger workflow: task 10 (the capstone)
uses it to turn a customer request into routable, typed data.

Demo to study first: `01-fundamentals/04_structured_output.py`.

## 📖 Official documentation

- [Structured Output](https://strandsagents.com/docs/user-guide/concepts/agents/structured-output/) — Pydantic models as agent output schemas
