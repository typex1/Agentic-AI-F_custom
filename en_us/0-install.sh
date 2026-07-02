#!/bin/bash
# Install uv/uvx (Python package manager and runner)
# https://github.com/astral-sh/uv

curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH for current session
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
uv --version
uvx --version
