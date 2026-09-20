# CV Match with Strands Agents

A [Langdock](https://www.langdock.com/) no-code workflow (six nodes; the original `jm_3.json`
export is not part of this repo) re-implemented as a Python workflow with the
[Strands Agents SDK](https://strandsagents.com). Same job: compare a CV against a job description,
rate every requirement with evidence, and compute a deterministic match score.

The example is built for teaching two things:

1. how a no-code workflow (trigger → code → agent → agent → code → output) translates into
   plain Python plus two `Agent` calls, and
2. how Strands **structured output** works, because both agent steps depend on it.

## The six steps

```
Langdock (no-code)                                Strands version (this folder)
------------------------------------------------  ---------------------------------------------------
1  form1   Form trigger: cv, jobDescription, notes  workflow.py        argparse / run(cv, jd, notes)
2  code2   Code "Read files"                        cv_match/files.py   read_text()
3  agent   "JD Requirement Extractor" (structured)  cv_match/agents.py  extract_requirements() -> JobRequirements
4  agent2  "Assess CV per requirement" (structured) cv_match/agents.py  assess_cv()            -> CVAssessment
5  code    Code "Compute score"                     cv_match/scoring.py compute_score()        -> ScoreResult
6  output  Output "Report"                          cv_match/report.py  render_report()        -> Markdown
```

`cv_match/schemas.py` holds the Pydantic models that replace the Langdock "Structured Output"
tables. `cv_match/prompts.py` holds the (lightly shortened) prompts of the two agent nodes.

Design principle kept from the original: the model judges, the code counts. The LLM decides
"how well does this CV cover requirement R10?", Python does the weighted arithmetic.

## Setup and run

This module uses the repo-level environment (see [`docs/setup.md`](../docs/setup.md)) — no
extra installs. Quickest way: `./0-start.sh` runs the sample pair and writes `report.md` /
`run.json` to `runs/<timestamp>/`. `./0-start.sh -m <bedrock-model-id> cv.txt jd.txt` picks
another model, `./0-start.sh --explain [--live]` runs the structured-output demo,
`./0-start.sh -h` lists all options. Manual steps:

Default model: `amazon.nova-lite-v1:0` (the only one permitted in the class environment);
override with `CV_MATCH_MODEL_ID` or `--model-id` — a stronger model (e.g. Claude Sonnet)
gives more precise ratings. `samples/sample_report.md` was produced with Claude Sonnet.

> **Nova Lite caveat (observed):** on the sample pair Nova Lite rated requirement R8
> (German C1 required, CV says B2) as fully met and returned verdict `strong` / 88 %, while
> Claude Sonnet caught the gap and returned `review`. Same code, same schema — a smaller
> model judges less carefully. Good classroom material: the schema guarantees the *shape*
> of the answer, never its *correctness*.

```bash
cd 06-cv-match
source ../.venv/bin/activate

# the full workflow on the sample pair
python workflow.py samples/CV_AI_engineer.txt samples/Job_Description_AI_engineer.txt \
    --out report.md --json run.json

# with the optional recruiter notes (Langdock form field "notes")
python workflow.py cv.txt jd.txt --notes "must-have: German C1"
```

`--json` writes every intermediate structured result (`requirements`, `assessment`, `score`) so
students can inspect what each step produced. `samples/sample_report.md` and
`samples/sample_run.json` are the output of one real run (about 35 s, 19 requirements,
85 % overall, 92 % must-haves, verdict `review` because German is B2 instead of C1). The
Langdock run of the same files gave 81 % / 92 % / `review`; the difference is model and run
variance, the verdict and the identified gap are the same.

## How Strands structured output works

Run `python explain_structured_output.py` (no AWS needed) and then
`python explain_structured_output.py --live` (one small Bedrock call). It shows the three
mechanics below on the real schemas of this project.

### 1. A Pydantic model is the contract

```python
class Requirement(BaseModel):
    id: str = Field(description="Sequential id: R1, R2, ...", pattern=r"^R\d+$")
    category: Literal["hard_skill", "experience", "education", "language", "soft_skill", "certification", "other"]
    priority: Literal["must", "nice"]
    weight: int = Field(ge=1, le=5, description="5 = central, 1 = peripheral")
    source: str = Field(description="Verbatim quote from the job description")

class JobRequirements(BaseModel):
    """Structured output of the JD Requirement Extractor agent."""
    role_title: str
    requirements: list[Requirement] = Field(min_length=1)
```

You pass it at call time (or as an agent default) and get an instance back:

```python
agent = Agent(system_prompt=EXTRACTOR_SYSTEM_PROMPT, model=BedrockModel(temperature=0.1))
result = agent(jd_text, structured_output_model=JobRequirements)
reqs: JobRequirements = result.structured_output      # typed object, already validated
reqs.requirements[0].weight                            # -> int, guaranteed 1..5
```

### 2. Under the hood it is a tool call, not "please answer in JSON"

Strands converts the Pydantic class into a **tool specification** (JSON Schema, see
`convert_pydantic_to_tool_spec`) and registers it as the one tool the model has to call to
finish. Docstrings become the tool description, `Field(description=...)` becomes property
descriptions, `Literal` becomes `enum`, `ge`/`le` become `minimum`/`maximum`, nested models
become nested object schemas, `min_length`/`max_length` on lists become `minItems`/`maxItems`.

Because every major provider (Bedrock, Anthropic, OpenAI, Gemini, ...) supports tool calling
with a JSON schema, this works for all Strands model providers. Bedrock can additionally
enforce the schema server-side with `BedrockModel(strict_tools=True)`.

### 3. Validation failures go back to the model, which retries

When the model calls the tool, Strands instantiates your Pydantic model with the arguments.
If that raises a `ValidationError`, the error text is returned to the model as a **tool
error** and the model gets another attempt. Part 3 of `explain_structured_output.py` shows
the real message history:

```
user      text        Record: text=Python, priority=must, weight=1
assistant toolUse     Weighted {"text": "Python", "priority": "must", "weight": 1}
user      toolResult  status=error: Validation failed for Weighted. ... must-have requirements need weight >= 3
assistant toolUse     Weighted {"text": "Python", "priority": "must", "weight": 3}
user      toolResult  status=success
```

This is why the validators in `schemas.py` are worth writing: a `@model_validator` that says
"a must-have needs weight >= 3" or "fulfilment > 0 needs a quoted evidence passage" is not just
documentation, it is enforced, and the error message is the instruction the model sees on
retry. If the model still cannot satisfy the schema, the call raises
`strands.types.exceptions.StructuredOutputException`.

### What the schema cannot do, and where that logic lives instead

Validators only see the one object being produced. The rule "exactly one assessment per
requirement id, in the same order" spans two agent calls, so `compute_score()` checks it in
code: unrated ids are scored 0 and listed under `unassessed_ids` in the report (this mirrors
the `"not assessed"` fallback of the Langdock Code node).

## Langdock vs Strands: what changed and why

| Aspect | Langdock workflow | Strands version |
|---|---|---|
| Output schema | Flat table (name, type, description); element shape of an Array only describable in prose | Real nested Pydantic models with enums, bounds, regex, validators |
| Guarantee | None; the Code node needed `as_list_of_dicts()` / `to_int()` to survive strings-in-lists and JSON-in-strings | Validated object or exception; scoring code shrinks by half |
| Passing data between steps | Template variables `{{agent?.output.structured.requirements}}` | Python objects; the assessor gets `reqs.requirements` serialised with `model_dump` |
| Reading files | Separate Code node because a FILE field interpolates as a file object | `Path.read_bytes()` |
| Instructions vs data | One prompt with the document interpolated inside | System prompt for the instructions, document in the user message |
| Model | Workspace model id (UUID) | `BedrockModel(model_id=..., temperature=0.1)`, swappable for any Strands provider |
| Running it | Form in the Langdock UI or `@CV Match` in chat | CLI, importable `run()` function, testable steps |

## Comparison with the official Strands workflow example

Strands ships a sequential-agents blueprint, `agents_workflow.py` (Researcher → Analyst → Writer,
[source](https://github.com/strands-agents/harness-sdk/blob/main/site/docs/examples/python/agents_workflow.py)).
Its structure: one `run_*_workflow()` function, agents created inline with a system prompt and
`callback_handler=None`, called in a fixed order, results passed on as `str(response)`.

`workflow_compact.py` is our workflow rewritten in exactly that single-file layout, with
`BLUEPRINT:` / `OURS:` comments at every point where the two differ. The architecture is the
same (plain Python orchestration, no `Graph` or `Swarm`); the deviations are:

- results are passed as validated Pydantic objects (`structured_output_model`) instead of prose,
- two deterministic Python steps (read files, compute score) sit between the agents,
- the report is a template, not a third "Writer" agent call,
- files come from the command line instead of an interactive `input()` loop.

`workflow.py` is the same thing split into modules; use whichever is easier to teach from.

## Ideas for exercises

- Tighten a validator (e.g. require `fulfilment == 3` for a must-have to count as covered, or
  reject `evidence` that is not a substring of the CV) and watch how the model reacts.
- Add `notes` as a form field replacement: pass `--notes "must-have: Kubernetes"` and check that
  the extractor promotes it to `must`.
- Replace `BedrockModel` with another provider (Anthropic, OpenAI) and compare scores.
- Turn the two agents into nodes of a Strands `Graph` (multi-agent pattern) instead of two
  sequential calls, and discuss what you gain and lose versus explicit Python orchestration.
- Enable `strict_tools=True` and inspect the request Bedrock receives.

## Caveats

- Ratings still come from a model. Low temperature and the 0-3 scale make them stable, not
  identical, across runs.
- CV screening is a high-risk use case under the EU AI Act and touches the German AGG. Keep the
  output as decision support with visible evidence per requirement, never as an automated
  rejection; the prompts restrict the model to job-related requirements.
- The sample CV and job description are fictitious.
