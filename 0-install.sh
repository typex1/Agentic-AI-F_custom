#!/bin/bash
# Install uv/uvx (Python package manager and runner)
# https://github.com/astral-sh/uv

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH for current session
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
uv --version
uvx --version

# Install Python dependencies
pip install -r "$SCRIPT_DIR/requirements.txt"
