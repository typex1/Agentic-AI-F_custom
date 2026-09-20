"""Build the pydantic_only.ipynb teaching notebook for 05-cv-match/pydantic/ with nbformat."""
import nbformat as nbf
from pathlib import Path

OUT = Path(__file__).parent

def nb(cells):
    n = nbf.v4.new_notebook()
    n.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    n.metadata["language_info"] = {"name": "python"}
    n.cells = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    return n

# ───────────────────────────── 1. pydantic_only.ipynb ─────────────────────────────
pyd = [
("md", """# Pydantic in isolation — NO LLM involved

This notebook is the step-by-step version of [`pydantic_only.py`](pydantic_only.py).

It uses **only pydantic**. There is no Strands agent and no network call, so every
cell runs instantly and for free. The goal: understand exactly what pydantic
contributes to Strands *structured output* — before any model gets involved.

Pydantic contributes three things, and we look at each in turn:

1. **Type coercion** — turning `"36"` into `36`
2. **Validation** — refusing what cannot be coerced, with a readable error
3. **JSON schema** — the machine-readable description of the model that Strands
   sends to the LLM as a *tool specification*"""),

("code", """import json

from pydantic import BaseModel, Field, ValidationError"""),

("md", """## The model

A pydantic model is a plain Python class that inherits from `BaseModel`. Each
class attribute with a type annotation becomes a **field**.

Two details matter for Strands later on:

- The **docstring** (`\"\"\"Model that contains …\"\"\"`) becomes the *description of
  the tool* the LLM will see.
- Each `Field(description=...)` becomes the *description of that parameter*.
  These descriptions are the only hints the model gets about what to put where —
  write them for the model, not for yourself.

This is the same `PersonInfo` class used in `structured_output.py`."""),

("code", """class PersonInfo(BaseModel):
    \"\"\"Model that contains information about a Person\"\"\"
    name: str = Field(description="Name of the person")
    age: int = Field(description="Age of the person")
    occupation: str = Field(description="Occupation of the person")"""),

("md", """## 1) Coercion: `"36"` becomes `36`

`age` is annotated as `int`, but we pass the **string** `"36"`. Pydantic does not
complain — it *coerces* the value to an `int` because the conversion is
unambiguous.

Why this matters for LLMs: models produce text. Even when a model is asked for a
number, the tool arguments may arrive as `"36"`. Coercion means your code still
gets a real `int` without you writing any parsing."""),

("code", """ada = PersonInfo(name="Ada", age="36", occupation="mathematician")
print(ada)
print(type(ada.age))  # <class 'int'> — not str"""),

("md", """## 2) Validation failure: `"thirty-six"` cannot become an `int`

Coercion has limits. There is no unambiguous way to turn `"thirty-six"` into an
integer, so pydantic raises a `ValidationError`.

Read the error message carefully — it names the **field** (`age`), the **problem**
(*unable to parse string as an integer*), and the **input** it received.

This message is the key to how Strands does structured output: when the LLM
produces an invalid value, Strands sends **exactly this text back to the model**
as a tool error, and the model gets another try. A good error message is
therefore an *instruction to the model*."""),

("code", """try:
    PersonInfo(name="Ada", age="thirty-six", occupation="x")
except ValidationError as e:
    print("Validation failed as expected:")
    print(e)"""),

("md", """## 3) The JSON schema — what Strands sends to the model

`model_json_schema()` turns the class into a **JSON Schema** document. Look at the
output and find:

- `"title": "PersonInfo"` — from the class name → becomes the **tool name**
- `"description": "Model that contains …"` — from the docstring → the **tool description**
- `"properties"` with `name` / `age` / `occupation`, each with its `type` and
  the `description` you wrote in `Field(...)`
- `"required": [...]` — all three fields, because none has a default

Strands wraps this schema as the `inputSchema` of a tool and offers that tool to
the LLM. The model never sees "please answer in JSON" — it sees a tool called
`PersonInfo` with three parameters, and it fills them in like any other tool call.
Pydantic then runs `PersonInfo(**arguments)` on what comes back — which is
exactly what we did by hand in steps 1 and 2."""),

("code", """print(json.dumps(PersonInfo.model_json_schema(), indent=2))"""),

("md", """## Summary

| Step | What pydantic did | Where Strands uses it |
|---|---|---|
| Coercion | `"36"` → `36` | Tool arguments from the model become typed Python values |
| Validation | `ValidationError` with a readable message | Sent back to the model as a tool error → model retries |
| JSON schema | `model_json_schema()` | Becomes the tool spec the model sees |

Nothing here needed an LLM. Continue with
[`01-fundamentals/04_structured_output.py`](../../01-fundamentals/04_structured_output.py)
to see the same idea used in a real agent call — and read
[`README.md`](README.md) for the Strands source code behind it."""),
]

nbf.write(nb(pyd), OUT / "pydantic_only.ipynb")
print("written:", OUT / "pydantic_only.ipynb")
