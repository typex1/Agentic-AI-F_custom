"""
04_structured_output.py — Structured Output with Pydantic

Demonstrates:
  - Getting typed, validated responses from agents
  - Using Pydantic models as output schemas
  - Accessing structured fields programmatically

Instead of parsing free-text responses, the Strands SDK lets you define
a Pydantic model and the agent returns data matching that schema.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from pydantic import BaseModel, Field
from strands import Agent


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


# --- Create agent with structured output ---
agent = Agent(
    model="amazon.nova-lite-v1:0",
    system_prompt="You are a knowledgeable assistant. Provide accurate, structured responses.",
    callback_handler=None,
)

# --- Get a typed book recommendation ---
print("=== Structured Output: Book Recommendation ===\n")
result = agent(
    "Recommend a classic science fiction novel.",
    structured_output_model=BookRecommendation,
)

# Access fields with full type safety
book = result.structured_output
print(f"Title:   {book.title}")
print(f"Author:  {book.author}")
print(f"Year:    {book.year}")
print(f"Genre:   {book.genre}")
print(f"Rating:  {book.rating}/5.0")
print(f"Summary: {book.summary}")

# --- Get a typed movie analysis ---
print("\n=== Structured Output: Movie Analysis ===\n")
result = agent(
    "Analyze the movie 'Inception' by Christopher Nolan.",
    structured_output_model=MovieAnalysis,
)

movie = result.structured_output
print(f"Title:    {movie.title}")
print(f"Director: {movie.director}")
print(f"Themes:   {', '.join(movie.themes)}")
print(f"Sentiment: {movie.sentiment}")
print(f"For:      {movie.recommended_for}")
