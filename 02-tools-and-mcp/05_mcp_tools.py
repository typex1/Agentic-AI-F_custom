"""
05_mcp_tools.py — Consuming Tools from an MCP Server

Demonstrates:
  - Connecting a Strands agent to a remote MCP server
  - Using the AWS Knowledge MCP server (no authentication required)
  - Discovering and using MCP-provided tools automatically
  - Direct MCP tool invocation

The Model Context Protocol (MCP) lets agents use tools hosted by external
servers. Here we connect to the AWS Knowledge MCP server, which exposes
tools for searching and reading official AWS documentation.

Server: https://knowledge-mcp.global.api.aws  (Streamable HTTP, public, rate-limited)
Tools provided:
  - search_documentation      : Search AWS docs, agent skills, Strands docs
  - read_documentation        : Retrieve an AWS/Strands page as markdown
  - list_regions              : List all AWS regions
  - get_regional_availability : Regional availability of services/APIs/resources
  - retrieve_skill            : Retrieve an AWS agent skill
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient


# --- Connect to the AWS Knowledge MCP server (remote, Streamable HTTP) ---
AWS_KNOWLEDGE_MCP_URL = "https://knowledge-mcp.global.api.aws"

aws_knowledge_client = MCPClient(
    lambda: streamablehttp_client(AWS_KNOWLEDGE_MCP_URL)
)


# --- MCP connections must be used within a context manager ---
with aws_knowledge_client:
    # Discover the tools the server provides
    tools = aws_knowledge_client.list_tools_sync()
    print("=== Tools Discovered from AWS Knowledge MCP Server ===\n")
    for t in tools:
        print(f"  • {t.tool_name}")
    print()

    # Create an agent that can use the MCP tools
    agent = Agent(
        model="amazon.nova-lite-v1:0",
        tools=tools,
        system_prompt=(
            "You are an AWS expert assistant. Use the AWS Knowledge tools to "
            "look up accurate, up-to-date information from official AWS docs. "
            "Cite what you find concisely."
        ),
        callback_handler=None,
    )

    # --- Query 1: The agent searches AWS docs automatically ---
    print("=== Query 1: Ask about an AWS service ===\n")
    response = agent(
        "What is Amazon Bedrock and what is the Converse API used for? "
        "Search the AWS documentation and summarize in 3-4 sentences."
    )
    print(f"{response}\n")

    # --- Query 2: Regional availability ---
    print("=== Query 2: Regional availability ===\n")
    response = agent(
        "Is Amazon Bedrock available in the us-east-1 region? "
        "Use the regional availability tool to check."
    )
    print(f"{response}\n")

    # --- Direct MCP tool invocation (bypasses agent reasoning) ---
    # Note: this server prefixes its tool names with "aws___"
    print("=== Direct MCP Tool Invocation: aws___list_regions ===\n")
    result = aws_knowledge_client.call_tool_sync(
        tool_use_id="direct-list-regions-1",
        name="aws___list_regions",
        arguments={},
    )
    # Print just the first chunk of the result
    text = result["content"][0]["text"]
    print(text[:500] + ("..." if len(text) > 500 else ""))

print("\n[MCP connection closed]")
