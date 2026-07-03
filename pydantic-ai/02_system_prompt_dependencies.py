from dataclasses import dataclass
import asyncio
import httpx
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

# official docs: https://pydantic.dev/docs/ai/core-concepts/dependencies/

# --- Configure the model: Amazon Bedrock + Nova Lite in us-east-1 ---
model = BedrockConverseModel(
    "amazon.nova-lite-v1:0",
    provider=BedrockProvider(region_name="us-east-1"),
)

@dataclass
class MyDeps:
  api_key: str
  http_client: httpx.AsyncClient


agent = Agent(
  model,
  deps_type=MyDeps,
)


@agent.system_prompt  
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  
  response = await ctx.deps.http_client.get(  
      'https://example.com',
      headers={'Authorization': f'Bearer {ctx.deps.api_key}'},  
  )
  response.raise_for_status()
  return f'Prompt: {response.text}'


async def main():
  async with httpx.AsyncClient() as client:
      deps = MyDeps('foobar', client)
      result = await agent.run('Tell me a joke.', deps=deps)
      print(result.output)
      #> Did you hear about the toothpaste scandal? They called it Colgate.


if __name__ == "__main__":
  asyncio.run(main())