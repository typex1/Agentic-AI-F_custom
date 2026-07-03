#!/bin/bash
# kiro-replica-cli.sh — thin launcher for the Kiro-Replica CLI (Task 1 solution).
#
# Starts an interactive terminal session with a Nova Lite agent that can run
# shell commands and search the web.
#
# Usage:
#   ./kiro-replica-cli.sh            # asks before running each shell command
#   ./kiro-replica-cli.sh --yolo     # runs shell commands without confirmation
#
# Requires: strands-agents, strands-agents-tools, ddgs  (see repo requirements.txt)
# Requires: AWS credentials with bedrock-runtime access to Nova Lite in us-east-1.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer python3, fall back to python.
PYTHON_BIN="$(command -v python3 || command -v python)"

exec "$PYTHON_BIN" "$SCRIPT_DIR/kiro_replica.py" "$@"
