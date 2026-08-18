# Setup Guide

## Prerequisites

- **Python 3.10+**
- **AWS Account** with Amazon Bedrock access ([create one here](https://aws.amazon.com/resources/create-account/?p=ft&z=subnav&loc=4))
- **AWS CLI** configured with credentials that have `bedrock-runtime:Converse` permission

## Quick Install

```bash
# Clone the repo
git clone https://github.com/typex1/Agentic-AI-F_custom.git
cd Agentic-AI-F_custom

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install non-pip tools (uv/uvx for MCP server)
./0-install.sh
```

## AWS Credentials

Make sure your environment has AWS credentials configured:

```bash
# Option 1: AWS CLI profile
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

### Required Permissions

The minimum IAM permission needed is:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock-runtime:Converse",
    "bedrock-runtime:ConverseStream",
    "bedrock-runtime:InvokeModel",
    "bedrock-runtime:InvokeModelWithResponseStream"
  ],
  "Resource": "*"
}
```

See [docs/model-permissions.md](model-permissions.md) for the full verified permission matrix.

## Model

All examples default to **Amazon Nova Lite** (`amazon.nova-lite-v1:0`) in `us-east-1`. You can swap to other models — see [02-tools-and-mcp/](../02-tools-and-mcp/) or the [reference course module on model providers](../reference/building-with-strands-course/samples/02-model-providers/).

## Alternative Model Providers (no AWS needed)

Strands is model-agnostic. You can use it without AWS:

| Provider | Install | Auth |
|----------|---------|------|
| Anthropic | `pip install "strands-agents[anthropic]"` | `ANTHROPIC_API_KEY` |
| OpenAI | `pip install "strands-agents[openai]"` | `OPENAI_API_KEY` |
| Ollama (local) | `pip install "strands-agents[ollama]"` | None — runs locally |

## MCP Server (optional)

The repo's `.kiro/settings/mcp.json` configures the **Strands Agents MCP server** (`uvx strands-agents-mcp-server`), giving AI coding assistants access to Strands documentation. This requires `uv`/`uvx` (installed by `0-install.sh`).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: strands` | Activate the venv: `source .venv/bin/activate` |
| `ThrottlingException` on Bedrock | Switch to `amazon.nova-lite-v1:0` or `amazon.nova-micro-v1:0` |
| Claude access error on first call | Wait 2 minutes and retry (one-time acknowledgment) |
| AWS credentials not found | Run `aws configure` or export env vars |
