# Task 2 — Reference Solution: Typed, Read-Only API Tools

Reference for [`../../tasks/2-typed-api-tools.md`](../../tasks/2-typed-api-tools.md).
Compare against this *after* attempting the task.

## Files

| File | Role |
|------|------|
| `station_api_server.py` | A stand-in "Rate-My-Station" REST API — an in-memory dataset served as JSON over `http.server`. Read-only. |
| `typed_tools_agent.py`  | Pydantic response models + typed `@tool` wrappers (calling the API over HTTP) + the Nova Lite agent. |

## Run

```bash
cd strands-agents/solutions/2-typed-api-tools
python typed_tools_agent.py          # starts the API in-process, then runs the agent
# (optional) run the API standalone to poke it by hand:
python station_api_server.py         # serves at http://127.0.0.1:8077
```

## What it demonstrates

- **Typed tools.** `list_stations`, `search_stations`, `get_station`,
  `get_ratings` — each type-hinted and validating its HTTP response into a
  Pydantic model (`StationSummary`, `StationDetail`, `StationRatings`) before
  returning. Bad data raises instead of leaking through.
- **The agent chains tools.** Q1 ("best cleanliness in Köln + its accessibility")
  makes the model `search_stations` → `get_ratings`, then reason over both.
- **Graceful failure.** Unknown ids return `{"error": ...}` (see Q2), so the
  agent says "not found" instead of crashing.
- **Typed final answer.** Q3 uses `structured_output_model=StationRecommendation`
  (demo 04 pattern) to return a validated object, not free text.
- **Read-only by design.** No endpoint or tool mutates data. Writing — with
  human-in-the-loop approval — is Task 4.

## Verified behaviour (Nova Lite)

```
Q1 -> Köln Messe/Deutz, accessibility 4.2   (search -> ratings, correct)
Q2 -> "station 999 does not exist"          (clean not-found)
Q3 -> StationRecommendation(name='Berlin Hauptbahnhof', accessibility=4.8, ...)
```

## Design notes

- The API is bound to `127.0.0.1` on an **ephemeral port** (`port=0`) in a daemon
  thread, so `typed_tools_agent.py` is a single self-contained command with no
  port clashes.
- Tools call the API with `urllib` (standard library) — no extra dependencies.
- `BASE_URL` is the only coupling to the data source: point it at the real
  Rate-My-Station API and the tools work unchanged.

## Prerequisites

- `pip install -r ../../../requirements.txt` (needs `strands-agents`, `pydantic`).
- AWS credentials with `bedrock-runtime` access to Nova Lite in `us-east-1`.
