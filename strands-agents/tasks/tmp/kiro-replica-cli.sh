#!/usr/bin/env bash
# kiro-replica-cli.sh — Thin launcher for the Kiro CLI replica agent
# Usage: ./kiro-replica-cli.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/kiro_replica.py" "$@"
