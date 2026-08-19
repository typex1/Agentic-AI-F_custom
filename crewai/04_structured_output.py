"""
04_structured_output.py — Structured Output with Pydantic

Demonstrates:
  - Getting typed, validated responses from agents
  - Using Pydantic models as output schemas
  - Accessing structured fields programmatically

Instead of parsing free-text responses, CrewAI lets you define a Pydantic
model and get data matching that schema back.

How this differs from Strands:
  - Strands: pass `structured_output_model=...` on the agent CALL, then read
    `result.structured_output`.
  - CrewAI: structured output is declared on the TASK via `output_pydantic=...`
    (fitting CrewAI's model where the Task, not the call, defines the work),
    then read `result.pydantic`. The raw text stays in `result.raw`.
  So the feature IS available in CrewAI — it just lives on the Task.
"""

import os
# Opt out of CrewAI telemetry/tracing before importing crewai (see 01_basic_agent.py).
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM


# --- Define your output schema ---
class BookRecommendation(BaseModel):
    """A book recommendation with structured fields."""
    title: str = Field(description="The book title")
    author: str = Field(description="The author's full name")
    year: int = Field(description="Publication year")
    genre: str = Field(description="Primary genre")
    summary: str = Field(description="One-sentence summary of the book")
    rating: float = Field(description="Rating out of 5.0", ge=0, le=5)


class MovieAnalysis(BaseModel):
    """Structured analysis of a movie."""
    title: str = Field(description="Movie title")
    director: str = Field(description="Director's name")
    themes: list[str] = Field(description="Main themes explored in the movie")
    sentiment: str = Field(description="Overall sentiment: positive, negative, or mixed")
    recommended_for: str = Field(description="Target audience description")


# --- Create the agent ---
llm = LLM(model="bedrock/amazon.nova-lite-v1:0")

agent = Agent(
    role="Knowledgeable Assistant",
    goal="Provide accurate, structured responses.",
    backstory="You are a knowledgeable assistant. Provide accurate, structured responses.",
    llm=llm,
    verbose=False,
)

# --- Get a typed book recommendation ---
# The schema is attached to the Task via output_pydantic.
print("=== Structured Output: Book Recommendation ===\n")
book_task = Task(
    description="Recommend a classic science fiction novel.",
    expected_output="A book recommendation matching the requested schema.",
    output_pydantic=BookRecommendation,
    agent=agent,
)
result = Crew(agents=[agent], tasks=[book_task], verbose=False).kickoff()

# Access fields with full type safety via result.pydantic
book = result.pydantic
print(f"Title:   {book.title}")
print(f"Author:  {book.author}")
print(f"Year:    {book.year}")
print(f"Genre:   {book.genre}")
print(f"Rating:  {book.rating}/5.0")
print(f"Summary: {book.summary}")

# --- Get a typed movie analysis ---
print("\n=== Structured Output: Movie Analysis ===\n")
movie_task = Task(
    description="Analyze the movie 'Inception' by Christopher Nolan.",
    expected_output="A movie analysis matching the requested schema.",
    output_pydantic=MovieAnalysis,
    agent=agent,
)
result = Crew(agents=[agent], tasks=[movie_task], verbose=False).kickoff()

movie = result.pydantic
print(f"Title:    {movie.title}")
print(f"Director: {movie.director}")
print(f"Themes:   {', '.join(movie.themes)}")
print(f"Sentiment: {movie.sentiment}")
print(f"For:      {movie.recommended_for}")
