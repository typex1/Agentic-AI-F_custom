"""Build the two teaching notebooks for 06-cv-match/pydantic/ with nbformat."""
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

Nothing here needed an LLM. Continue with [`structured_output.ipynb`](structured_output.ipynb)
to see the same class used in a real agent call — and read
[`README.md`](README.md) for the Strands source code behind it."""),
]

# ───────────────────────────── 2. structured_output.ipynb ─────────────────────────────
so = [
("md", """# Strands structured output — step by step

This notebook is the step-by-step version of [`structured_output.py`](structured_output.py).

Unlike the pydantic-only notebook, this one **does call an LLM**: `agent(...)`
sends a prompt to Amazon Bedrock and Strands returns a validated `PersonInfo`
object instead of free text.

**Requirements:** AWS credentials with access to `amazon.nova-lite-v1:0`
(the only model permitted in the class environment). Run the cells in order."""),

("code", """from pydantic import BaseModel, Field
from strands import Agent"""),

("md", """## 1) Define the pydantic model — the contract

This is the *same* class as in `pydantic_only.ipynb`. Nothing about it is
Strands-specific: it is a plain pydantic model.

What changes is its *role*. Here it acts as the **contract** between your code
and the LLM: you tell Strands "the answer must have this shape", and Strands
guarantees you get back either an instance of this class or an exception —
never a string you have to parse.

Remember: the docstring and the `Field(description=...)` texts are what the
model reads. They are your only way to explain the fields to it."""),

("code", """class PersonInfo(BaseModel):
    \"\"\"Model that contains information about a Person\"\"\"
    name: str = Field(description="Name of the person")
    age: int = Field(description="Age of the person")
    occupation: str = Field(description="Occupation of the person")"""),

("md", """## 2) Create the agent

A minimal agent: just a model id. No tools, no system prompt.

Note what is **not** here: we do not tell the agent about `PersonInfo` yet. The
output model is passed *per call*, in the next step — the same agent can return
different shapes for different questions. (You can also set a default with
`Agent(structured_output_model=...)` if one agent always returns the same shape.)"""),

("code", """agent = Agent(
    model="amazon.nova-lite-v1:0"  # the only model permitted in this environment
)"""),

("md", """## 3) Call the agent with `structured_output_model=`

This is the one line that turns a chat agent into a structured-data extractor.

What happens inside Strands when this cell runs
(details with source references in [`README.md`](README.md)):

1. `PersonInfo.model_json_schema()` is converted into a **tool specification**
   named `PersonInfo`.
2. That tool is offered to the model, and the model is required to call it to
   finish its answer.
3. The model responds with a `toolUse` block: `PersonInfo(name=..., age=..., occupation=...)`.
4. Strands runs `PersonInfo(**arguments)` — pydantic coerces and validates.
5. If validation fails, the error text goes back to the model as a tool error
   and the model retries. If it succeeds, the instance is stored in
   `result.structured_output`.

Watch the cell output: you should see the tool call happening
(`Tool #1: PersonInfo`) before the final result."""),

("code", """# Spec: https://strandsagents.com/docs/api/python/strands.agent.agent/
result = agent(
    "John Smith is a 30 year-old software engineer",
    structured_output_model=PersonInfo
)"""),

("md", """## 4) Use the result — typed fields, no parsing

`result.structured_output` **is a `PersonInfo` instance**. You access fields as
attributes, and `age` is already an `int` — no `json.loads`, no regex, no
`int(...)` conversion.

Compare this to the alternative: asking the model "reply in JSON" and hoping the
reply parses. Here the shape is *enforced*, not *requested*."""),

("code", """person_info: PersonInfo = result.structured_output

print(f"Name: {person_info.name}")       # "John Smith"
print(f"Age:  {person_info.age}")        # 30  (an int!)
print(f"Job:  {person_info.occupation}") # "software engineer"
print()
print(type(person_info), "| age is", type(person_info.age).__name__)"""),

("md", """## 5) Look under the hood: the message history

Everything above was "ordinary tool calling". We can prove it by inspecting the
agent's conversation history. Look for:

- an **assistant** message containing a `toolUse` block with `name: PersonInfo`
  and your three fields as `input`
- a **user** message containing the matching `toolResult`

That tool call *is* the structured output. Pydantic just ran on its arguments."""),

("code", """import json

for msg in agent.messages:
    for block in msg["content"]:
        if "toolUse" in block:
            print(f"[{msg['role']}] toolUse  name={block['toolUse']['name']}")
            print("           input =", json.dumps(block["toolUse"]["input"]))
        elif "toolResult" in block:
            print(f"[{msg['role']}] toolResult status={block['toolResult']['status']}")
        elif "text" in block and block["text"].strip():
            print(f"[{msg['role']}] text     {block['text'][:80]!r}")"""),

("md", """## Try it yourself

- Change the prompt to *"Ada Lovelace, born 1815, wrote the first algorithm"* —
  there is no explicit age. What does the model put into `age`? (The schema
  guarantees an `int`, not that the `int` is *right*.)
- Add `age: int = Field(description=..., ge=0, le=120)` and give the model an
  absurd age in the prompt. Re-run step 5 and look for a `toolResult` with
  `status=error` followed by a second `toolUse` — that is the retry loop.
- Add a fourth field with a `Literal[...]` type and see how it appears as an
  `enum` in `PersonInfo.model_json_schema()`.

Next: [`../explain_structured_output.py`](../explain_structured_output.py) shows
the retry loop on the real CV-match schemas, and
[`../workflow.py`](../workflow.py) chains two structured-output agents into a
complete workflow."""),
]

nbf.write(nb(pyd), OUT / "pydantic_only.ipynb")
nbf.write(nb(so), OUT / "structured_output.ipynb")
print("written:", OUT / "pydantic_only.ipynb", OUT / "structured_output.ipynb")
