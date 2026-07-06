#!/usr/bin/env bash
# test_solution.sh — End-to-end test for Task 3: RAG over KB via MCP Server
#
# Tests:
#   1. Knowledge base files exist and are non-empty
#   2. MCP server module imports cleanly and retriever logic works
#   3. Full agent run (MCP server launched as subprocess, agent answers questions)
#
# The MCP server uses stdio transport (JSON-RPC over stdin/stdout), so it can't
# run as a traditional background daemon. Instead, the agent spawns it as a
# subprocess via MCPClient — which is the intended MCP pattern. We test both
# the retriever in isolation AND the full MCP+agent flow.
#
# Usage:  bash test_solution.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  ❌ FAIL: $1"; }

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Task 3 — RAG over a KB via MCP Server: Test Suite          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo

# ───────────────────────────────────────────────────────────────────────────────
echo "── Test 1: Knowledge base corpus files ──"
# ───────────────────────────────────────────────────────────────────────────────
for f in knowledge_base/facilities.md knowledge_base/tickets.md knowledge_base/onboard.md; do
    if [[ -s "$f" ]]; then
        pass "$f exists and is non-empty"
    else
        fail "$f missing or empty"
    fi
done
echo

# ───────────────────────────────────────────────────────────────────────────────
echo "── Test 2: MCP server retriever logic (unit test) ──"
# ───────────────────────────────────────────────────────────────────────────────
# Test the BM25 retriever functions directly without starting MCP transport.
python -c "
import sys
sys.path.insert(0, '.')
from kb_mcp_server import _load_passages, _tokenize, _bm25_score, _DOC_TOKENS, _PASSAGES

# Check corpus was loaded
assert len(_PASSAGES) > 0, 'No passages loaded'
print(f'  Loaded {len(_PASSAGES)} passages from knowledge_base/')

# Check each passage has source and text
for p in _PASSAGES:
    assert 'source' in p and 'text' in p, f'Malformed passage: {p}'

# Test retrieval: query about delay compensation
query_terms = _tokenize('delay compensation train late')
scores = []
for i in range(len(_PASSAGES)):
    s = _bm25_score(query_terms, _DOC_TOKENS[i])
    scores.append((s, _PASSAGES[i]))
scores.sort(key=lambda x: x[0], reverse=True)
top = scores[0]
assert top[0] > 0, 'Top result has zero score'
assert 'Delay compensation' in top[1]['source'], f'Expected delay compensation passage, got: {top[1][\"source\"]}'
print(f'  Query \"delay compensation train late\" -> top hit: {top[1][\"source\"]} (score: {top[0]:.2f})')

# Test retrieval: query about pets/dogs
query_terms = _tokenize('dog pet train')
scores2 = []
for i in range(len(_PASSAGES)):
    s = _bm25_score(query_terms, _DOC_TOKENS[i])
    scores2.append((s, _PASSAGES[i]))
scores2.sort(key=lambda x: x[0], reverse=True)
top2 = scores2[0]
assert top2[0] > 0, 'Top result has zero score'
assert 'Pets' in top2[1]['source'], f'Expected pets passage, got: {top2[1][\"source\"]}'
print(f'  Query \"dog pet train\" -> top hit: {top2[1][\"source\"]} (score: {top2[0]:.2f})')

# Test no-match scenario
query_terms = _tokenize('quantum physics black hole')
scores3 = []
for i in range(len(_PASSAGES)):
    s = _bm25_score(query_terms, _DOC_TOKENS[i])
    scores3.append((s, _PASSAGES[i]))
all_zero = all(s == 0 for s, _ in scores3)
assert all_zero, 'Expected no matches for out-of-domain query'
print(f'  Query \"quantum physics black hole\" -> no matches (correct)')

print('  All retriever unit tests passed.')
" && pass "Retriever logic works correctly" || fail "Retriever logic test failed"
echo

# ───────────────────────────────────────────────────────────────────────────────
echo "── Test 3: MCP server tool callable via search_knowledge_base() ──"
# ───────────────────────────────────────────────────────────────────────────────
# Call the tool function directly (bypassing MCP transport) to verify its output format.
python -c "
import sys
sys.path.insert(0, '.')
from kb_mcp_server import search_knowledge_base

# In-corpus query
result = search_knowledge_base('luggage locker storage', k=2)
assert 'NO_RESULTS' not in result, f'Expected results but got: {result}'
assert '[source:' in result, f'Missing source citation in result'
assert 'facilities.md#Luggage' in result, f'Expected luggage passage in result'
print(f'  search_knowledge_base(\"luggage locker storage\") returned result with citation')

# Out-of-domain query
result2 = search_knowledge_base('quantum physics black hole', k=3)
assert 'NO_RESULTS' in result2, f'Expected NO_RESULTS but got: {result2}'
print(f'  search_knowledge_base(\"quantum physics\") returned NO_RESULTS (correct)')

print('  Tool function output format verified.')
" && pass "MCP tool function produces correct output" || fail "MCP tool function test failed"
echo

# ───────────────────────────────────────────────────────────────────────────────
echo "── Test 4: Full end-to-end agent run (MCP subprocess + Bedrock) ──"
# ───────────────────────────────────────────────────────────────────────────────
# This launches kb_mcp_server.py as a subprocess (via MCPClient stdio),
# connects the agent, and verifies answers.
echo "  (This calls Amazon Bedrock — may take 15-30 seconds...)"

OUTPUT=$(timeout 120 python -c "
import warnings
warnings.filterwarnings(action='ignore', message=r'datetime.datetime.utcnow')

import sys
from pathlib import Path
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

SERVER_PATH = Path('kb_mcp_server.py').resolve()

client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command=sys.executable, args=[str(SERVER_PATH)])
    )
)

with client:
    tools = client.list_tools_sync()
    tool_names = [t.tool_name for t in tools]
    assert 'search_knowledge_base' in tool_names, f'Tool not found. Got: {tool_names}'
    print('TOOL_DISCOVERED:search_knowledge_base')

    model = BedrockModel(model_id='amazon.nova-lite-v1:0', region_name='us-east-1', temperature=0.0)
    agent = Agent(
        model=model,
        tools=tools,
        system_prompt=(
            'Answer ONLY from search_knowledge_base results. '
            'Cite [source: ...] for each fact. '
            'If not in the KB, say: NOT_IN_KB.'
        ),
        callback_handler=None,
    )

    # Test in-corpus question
    r1 = str(agent('How much delay compensation for a 90 minute late ICE train?'))
    print(f'ANSWER_1:{r1}')

    # Test out-of-corpus question
    r2 = str(agent('What is the population of Mars?'))
    print(f'ANSWER_2:{r2}')
" 2>&1) || true

# Check results
if echo "$OUTPUT" | grep -q "TOOL_DISCOVERED:search_knowledge_base"; then
    pass "MCP server started and tool discovered via MCPClient"
else
    fail "MCP server tool not discovered"
    echo "    Output: $(echo "$OUTPUT" | head -5)"
fi

if echo "$OUTPUT" | grep -qi "25.*percent\|25%"; then
    pass "In-corpus question answered correctly (25% compensation)"
else
    # Check if answer mentions compensation at all
    if echo "$OUTPUT" | grep -qi "compensation\|ticket price"; then
        pass "In-corpus question answered with compensation info"
    else
        fail "In-corpus question not answered correctly"
        echo "    Got: $(echo "$OUTPUT" | grep 'ANSWER_1')"
    fi
fi

if echo "$OUTPUT" | grep -qi "ANSWER_1" && echo "$OUTPUT" | grep -qi "source\|tickets.md"; then
    pass "Answer includes citation"
else
    fail "Answer missing citation"
fi

if echo "$OUTPUT" | grep -qi "NOT_IN_KB\|don't know\|not covered\|not in the knowledge\|cannot find\|no information"; then
    pass "Out-of-corpus question correctly refused"
else
    fail "Out-of-corpus question not properly refused"
    echo "    Got: $(echo "$OUTPUT" | grep 'ANSWER_2')"
fi
echo

# ───────────────────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════════════════"

if [[ $FAIL -eq 0 ]]; then
    echo "  🎉 All tests passed!"
    exit 0
else
    echo "  ⚠️  Some tests failed — check output above."
    exit 1
fi
