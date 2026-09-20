#!/usr/bin/env bash
# Start the CV Match workflow (Strands Agents port of a Langdock no-code workflow).
#
# Usage:
#   ./0-start.sh                                   # sample CV + sample job description, default model
#   ./0-start.sh -m us.anthropic.claude-haiku-4-5-20251001-v1:0
#   ./0-start.sh -m global.anthropic.claude-sonnet-4-6 my_cv.txt my_jd.txt
#   ./0-start.sh -n "must-have: German C1" my_cv.txt my_jd.txt
#   ./0-start.sh --explain                         # structured-output demo, offline parts only
#   ./0-start.sh --explain --live                  # ... plus the live validation-retry demo
#
# Options:
#   -m, --model-id ID   Bedrock model id (default: $CV_MATCH_MODEL_ID or amazon.nova-lite-v1:0)
#   -n, --notes TEXT    Extra recruiter constraints (Langdock form field "notes")
#   -o, --out-dir DIR   Where report.md / run.json are written (default: ./runs/<timestamp>)
#   -h, --help          Show this help
#
# Positional arguments: CV file, job description file (.txt). Defaults to the two files in samples/.
# Requires AWS credentials with Bedrock access (aws sts get-caller-identity should work).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODEL_ID="${CV_MATCH_MODEL_ID:-amazon.nova-lite-v1:0}"
NOTES=""
OUT_DIR=""
EXPLAIN=0
LIVE=""
POSITIONAL=()

usage() { sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--model-id) MODEL_ID="$2"; shift 2 ;;
    -n|--notes)    NOTES="$2"; shift 2 ;;
    -o|--out-dir)  OUT_DIR="$2"; shift 2 ;;
    --explain)     EXPLAIN=1; shift ;;
    --live)        LIVE="--live"; shift ;;
    -h|--help)     usage; exit 0 ;;
    -*)            echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    *)             POSITIONAL+=("$1"); shift ;;
  esac
done

CV="${POSITIONAL[0]:-samples/CV_AI_engineer.txt}"
JD="${POSITIONAL[1]:-samples/Job_Description_AI_engineer.txt}"

# --- Python environment: reuse the repo-level .venv (see ../docs/setup.md) ----
# Falls back to the active `python` if the repo venv does not exist.
if [[ -x ../.venv/bin/python ]]; then
  PY=../.venv/bin/python
else
  PY="$(command -v python)"
fi

# --- Structured-output demo ----------------------------------------------------
if [[ $EXPLAIN -eq 1 ]]; then
  echo ">> Model: $MODEL_ID" >&2
  CV_MATCH_MODEL_ID="$MODEL_ID" exec "$PY" explain_structured_output.py $LIVE
fi

# --- Workflow ------------------------------------------------------------------
[[ -f "$CV" ]] || { echo "CV file not found: $CV" >&2; exit 1; }
[[ -f "$JD" ]] || { echo "Job description file not found: $JD" >&2; exit 1; }

OUT_DIR="${OUT_DIR:-runs/$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$OUT_DIR"

echo ">> Model: $MODEL_ID" >&2
echo ">> CV:    $CV" >&2
echo ">> JD:    $JD" >&2
[[ -n "$NOTES" ]] && echo ">> Notes: $NOTES" >&2
echo ">> Out:   $OUT_DIR/report.md, $OUT_DIR/run.json" >&2
echo >&2

"$PY" workflow.py "$CV" "$JD" \
  --model-id "$MODEL_ID" \
  --notes "$NOTES" \
  --out "$OUT_DIR/report.md" \
  --json "$OUT_DIR/run.json"
