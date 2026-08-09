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

# Install tree command
sudo yum install tree -y

# Install Python dependencies.
# Use `python3 -m pip` so packages land in the same interpreter that will run
# the demos (a bare `pip` can belong to a different Python).
# strands-agents requires Python >= 3.10; this box also has a legacy
# /usr/bin/python3 (3.9), so guard against installing into the wrong one.
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "ERROR: 'python3' resolves to $(command -v python3) ($(python3 -V))," >&2
    echo "but strands-agents requires Python >= 3.10." >&2
    echo "Run the demos and this installer with Python 3.12, e.g.: python3.12" >&2
    exit 1
fi
echo "Installing dependencies for: $(command -v python3) ($(python3 -V))"
python3 -m pip install -r "$SCRIPT_DIR/requirements.txt"
