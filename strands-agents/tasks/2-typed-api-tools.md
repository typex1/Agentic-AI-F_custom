# Task 2 — Typed, Read-Only API Tools

## Goal

Wire up the **agent loop** against a real API and give your agent a set of
**typed, read-only tools**. This is the jump from "an agent that chats" to "an
agent that looks things up in a system of record."

You'll bind the **Rate-My-Station** API (a service that stores train-station
ratings) as a small toolbox: each tool is a plain Python function whose inputs
and outputs are described with **Pydantic** types, so the model gets a precise,
self-documenting schema and you get validation for free.

Read-only is deliberate. Writing (submitting a rating) is powerful and risky —
we add that *with guardrails* in Task 4. Here we focus on clean, typed reads.

Builds on demos `02_custom_tools.py` (the `@tool` decorator) and
`03_structured_output.py` (Pydantic models).

## Background: why typed tools?

The `@tool` decorator turns a function's signature, type hints, and docstring
into the JSON schema the model uses to decide *how* to call the tool. If your
tool takes a `station_id: int` and returns a well-defined object, the model
calls it correctly and can chain calls together. If everything is loose strings,
the model guesses — and guesses wrong. Types are how you make tool use reliable.

## What you build

1. **A stand-in Rate-My-Station API.** This repo doesn't ship the real service,
   so run a tiny local HTTP API (Python's standard-library `http.server` is
   enough) that serves station data as JSON. Treat it as a black-box REST API.
   *(If you have access to the real Rate-My-Station API, just point your tools
   at its base URL instead — the tools shouldn't care.)*
2. **Typed read tools** that call that API over HTTP and validate the responses
   into Pydantic models. Suggested toolbox:
   - `list_stations()` → list of station summaries
   - `search_stations(query)` → stations matching a name/city
   - `get_station(station_id)` → full detail for one station
   - `get_ratings(station_id)` → the rating breakdown (cleanliness, safety,
     accessibility, punctuality, …)
3. **An agent** (`amazon.nova-lite-v1:0`) with those tools that answers
   natural-language questions by choosing and chaining the right calls.

## Suggested structure

```
solutions/2-typed-api-tools/     # reference lives here; put your work alongside
  station_api_server.py          # the local mock API (JSON over HTTP)
  typed_tools_agent.py           # Pydantic models + @tool wrappers + the agent
```

## Functional requirements

- The agent uses **only** Nova Lite (`amazon.nova-lite-v1:0`).
- Every tool has **type-hinted parameters** and validates its API response into a
  **Pydantic model** before returning (a malformed response should raise, not
  silently pass through).
- All tools are **read-only** — no endpoint that mutates data.
- The agent answers a **multi-step** question that requires chaining ≥2 tools,
  e.g. *"Find the station in Cologne with the best cleanliness rating and tell me
  its accessibility score."* (search → get_ratings).
- Questions about unknown stations are handled gracefully (no crash).

## Hints

- Keep the API dumb and separate: a `station_api_server.py` that serves a small
  in-memory dataset. Bind it to `127.0.0.1` on an ephemeral port and start it in
  a background (daemon) thread so the agent script is a single `python` command.
- Call the API with `urllib.request` from inside your tools — no extra
  dependencies needed. Parse with `Model.model_validate(json_dict)`.
- Return `model.model_dump()` (a dict) or a short formatted string from each
  tool. The model reads either fine; a dict keeps the structure explicit.
- Give each tool a crisp docstring — it's part of the prompt the model sees.
- For a clean final answer, try `agent(question, structured_output_model=...)`
  (see demo 03) to get a typed result object back.

## Acceptance criteria

- [ ] A local API serves station data as JSON and the agent never talks to it
      except through your tools.
- [ ] Each tool is typed and validates responses into a Pydantic model.
- [ ] The agent answers a 2-step question by chaining tools (e.g. search →
      ratings) with a correct result.
- [ ] Asking about a non-existent station yields a clean "not found," not a
      stack trace.

## Stretch goals (optional)

- Add `structured_output_model` so the final answer is a typed object
  (e.g. `StationRecommendation(name, city, cleanliness, reason)`).
- Add pagination or a `min_rating` filter to `search_stations` and let the model
  use it.
- Point the tools at the *real* Rate-My-Station API by changing only the base
  URL — prove your tool layer is decoupled from the data source.

## Reflection questions

1. What exactly does the model "see" about each tool? Where does that schema come
   from?
2. Why validate the API response into a Pydantic model inside the tool instead of
   handing the raw JSON to the model?
3. You kept these tools read-only on purpose. What would change — in risk and in
   design — the moment one tool could *submit* a rating? (Task 4 picks this up.)
