"""
typed_tools_agent.py — Typed, read-only API tools (Task 2 reference solution)

Binds the local "Rate-My-Station" API (see station_api_server.py) to a Nova Lite
agent as a set of typed `@tool` functions. Each tool:
  - takes type-hinted parameters (so the model gets a precise call schema),
  - calls the API over HTTP with urllib (no extra dependencies),
  - validates the JSON response into a Pydantic model (bad data raises), and
  - returns a plain dict the model can reason over.

All tools are READ-ONLY. Writing a rating is a Task 4 concern (it needs
guardrails). The agent chains these reads to answer natural-language questions.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import json
import urllib.request
import urllib.parse
from typing import Optional

from pydantic import BaseModel, Field
from strands import Agent, tool
from strands.models import BedrockModel

import station_api_server

MODEL_ID = "amazon.nova-lite-v1:0"
AWS_REGION = "us-east-1"

# The API base URL is filled in at startup. Point this at the REAL
# Rate-My-Station API instead and the tools below work unchanged.
BASE_URL: str = ""


# --------------------------------------------------------------------------- #
# Typed response models (the "shape" of the API)
# --------------------------------------------------------------------------- #
class StationSummary(BaseModel):
    """A station as it appears in list/search results."""
    id: int
    name: str
    city: str


class StationRatings(BaseModel):
    """Per-category ratings for a station, each 0.0-5.0."""
    station_id: int
    cleanliness: float = Field(ge=0, le=5)
    safety: float = Field(ge=0, le=5)
    accessibility: float = Field(ge=0, le=5)
    punctuality: float = Field(ge=0, le=5)


class StationDetail(BaseModel):
    """Full detail for a single station."""
    id: int
    name: str
    city: str
    lines: list[str]
    review_count: int
    ratings: dict[str, float]


class StationRecommendation(BaseModel):
    """Typed final answer (used via structured_output_model)."""
    name: str = Field(description="Station name")
    city: str = Field(description="City the station is in")
    cleanliness: float = Field(description="Cleanliness rating 0-5")
    accessibility: float = Field(description="Accessibility rating 0-5")
    reason: str = Field(description="One sentence: why this station was chosen")


# --------------------------------------------------------------------------- #
# HTTP helper + a small error the tools can return cleanly
# --------------------------------------------------------------------------- #
class StationNotFound(Exception):
    pass


def _get(path: str, **params) -> object:
    """GET {BASE_URL}{path}?params and return parsed JSON. Raises on HTTP 404."""
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise StationNotFound(json.loads(e.read().decode("utf-8")).get("error", "not found"))
        raise


# --------------------------------------------------------------------------- #
# Read-only tools (typed in, validated out)
# --------------------------------------------------------------------------- #
@tool
def list_stations() -> list[dict]:
    """List all known stations (id, name, city). No arguments.

    Returns:
        A list of station summaries.
    """
    raw = _get("/stations")
    return [StationSummary.model_validate(s).model_dump() for s in raw]


@tool
def search_stations(query: str) -> list[dict]:
    """Search stations whose name or city contains the query text.

    Args:
        query: Free text to match against station name or city (e.g. "Köln").

    Returns:
        A list of matching station summaries (empty if none match).
    """
    raw = _get("/stations/search", q=query)
    return [StationSummary.model_validate(s).model_dump() for s in raw]


@tool
def get_station(station_id: int) -> dict:
    """Get full detail for one station (lines, review count, ratings).

    Args:
        station_id: The numeric station id (from list/search results).

    Returns:
        The station detail, or a {"error": ...} dict if the id is unknown.
    """
    try:
        raw = _get(f"/stations/{station_id}")
    except StationNotFound as e:
        return {"error": str(e)}
    return StationDetail.model_validate(raw).model_dump()


@tool
def get_ratings(station_id: int) -> dict:
    """Get the per-category rating breakdown for a station.

    Args:
        station_id: The numeric station id (from list/search results).

    Returns:
        The ratings (cleanliness, safety, accessibility, punctuality), or a
        {"error": ...} dict if the id is unknown.
    """
    try:
        raw = _get(f"/stations/{station_id}/ratings")
    except StationNotFound as e:
        return {"error": str(e)}
    return StationRatings.model_validate(raw).model_dump()


SYSTEM_PROMPT = (
    "You are a rail-travel assistant for the Rate-My-Station service. Answer "
    "questions about train stations using ONLY the provided tools — never invent "
    "stations or ratings. Typical flow: search or list to find a station id, then "
    "fetch its detail or ratings. Ratings are 0-5 (higher is better). Be concise."
)


def build_agent() -> Agent:
    model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.0)
    return Agent(
        model=model,
        tools=[list_stations, search_stations, get_station, get_ratings],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )


def main() -> None:
    global BASE_URL
    BASE_URL, _httpd = station_api_server.start_server()
    print(f"[setup] Rate-My-Station API running at {BASE_URL}\n")

    agent = build_agent()

    # 1) Multi-step: search -> ratings (chains at least two tools).
    q1 = ("Among the stations in Köln, which has the best cleanliness rating, "
          "and what is that station's accessibility score?")
    print(f"Q1: {q1}")
    print(f"A1: {agent(q1)}\n{'-' * 70}")

    # 2) Graceful handling of an unknown station.
    q2 = "What are the ratings for station id 999?"
    print(f"Q2: {q2}")
    print(f"A2: {agent(q2)}\n{'-' * 70}")

    # 3) Typed final answer via structured_output_model (see demo 03).
    q3 = "Recommend the single best station overall for a wheelchair user, considering accessibility."
    print(f"Q3: {q3}")
    result = agent(q3, structured_output_model=StationRecommendation)
    rec = result.structured_output
    print("A3 (typed StationRecommendation):")
    print(f"     name={rec.name!r} city={rec.city!r} "
          f"cleanliness={rec.cleanliness} accessibility={rec.accessibility}")
    print(f"     reason={rec.reason!r}")


if __name__ == "__main__":
    main()
