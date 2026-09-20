"""Pydantic in isolation - NO LLM involved.

This script uses only pydantic. There is no Strands agent and no network call,
so it runs instantly and for free. It shows what pydantic contributes to Strands
structured output (see 01-fundamentals/04_structured_output.py for the agent
side): type coercion, validation, and the JSON schema that Strands sends to
the model.

New to pydantic? Start here. The notebook version pydantic_only.ipynb explains
each chunk.
"""

import json

from pydantic import BaseModel, Field, ValidationError


# The same model used in the Strands example.
class PersonInfo(BaseModel):
    """Model that contains information about a Person"""
    name: str = Field(description="Name of the person")
    age: int = Field(description="Age of the person")
    occupation: str = Field(description="Occupation of the person")


# 1) Coercion: the string "36" is accepted and converted to the int 36.
ada = PersonInfo(name="Ada", age="36", occupation="mathematician")
print(ada)  # age is now 36 (an int)

# 2) Validation failure: "thirty-six" can't become an int, so pydantic raises.
#    We catch it so the script keeps running and we can read the error.
try:
    PersonInfo(name="Ada", age="thirty-six", occupation="x")
except ValidationError as e:
    print("Validation failed as expected:")
    print(e)

# 3) The JSON schema that Strands sends to the model.
print(json.dumps(PersonInfo.model_json_schema(), indent=2))
