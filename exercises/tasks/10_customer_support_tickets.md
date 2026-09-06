# Task: Customer support ticket resolution — all four patterns in one workflow (capstone)

Build an agentic workflow with the **Strands Agents SDK** that resolves the
customer request below by combining all four agent workflow patterns:
**Chaining, Parallelization, Orchestration, Routing**.

This is the capstone exercise — it assumes you have completed task sheets
01–05. Working materials (data generator + mock backend data) live in
[`10_customer_support_tickets_data/`](10_customer_support_tickets_data/).

## Why this exercise: genuine pattern integration

The four patterns don't run side by side — they operate *within* one workflow:

- **Orchestration** doesn't just coordinate — it creates a plan to handle
  multiple customer goals simultaneously.
- **Routing** determines the workflow path based on case complexity,
  directly affecting which chain executes.
- **Chaining** provides overall structure, while **parallelization** happens
  *inside* the assess-situation step — four backend systems are queried
  simultaneously without breaking the sequential flow.
- When orchestration analyzes the parallel results and discovers VIP status,
  it triggers routing to the premium path, which activates a completely
  different chain.

The customer should experience one smooth interaction; behind the scenes all
four patterns coordinate to resolve multiple issues efficiently. That
integration is what makes agentic systems intelligent rather than just
automated.

## The canonical request

> "Customer C001 here about order O1001: My order never arrived, I need a
> refund, but I also want to reorder if you have stock."

Expected behavior: your workflow identifies C001 as a **VIP** with a **valid
claim** (parcel lost) and **stock available**, routes the case to the
**premium** path, and executes the VIP chain — approve refund → process
payment immediately → create an express replacement order → provide a
tracking link — finishing with one friendly customer-facing reply.

A different request must take a different path (that's what makes routing
real). Your solution must handle at least these three routes:

| Route | Trigger | Example |
|---|---|---|
| premium | VIP + valid claim | C001 / O1001 |
| standard | valid claim, not VIP | C002 / O1002 |
| escalation | invalid or suspicious claim | C003 / O1003 (carrier says delivered) |

## Setup

```bash
cd 10_customer_support_tickets_data
python generate_data.py     # creates data/ — run it again anytime to RESET
```

This gives you four JSON files, one per mock backend system:

| File | System | Used for |
|---|---|---|
| `data/customers.json` | CRM | customer status check (tier: vip/standard) |
| `data/orders.json` | Order management | order tracking check |
| `data/inventory.json` | Warehouse | inventory check |
| `data/refunds.json` | Billing | refund eligibility check (policy block) + refund history |

Model: `amazon.nova-lite-v1:0` (the only one permitted in this environment).

## Requirements — the four steps

1. **Step 1 — Assess situation** *(Chaining + Parallelization)*:
   query all four systems for the customer/order **concurrently**:
   customer status, order tracking, inventory, refund eligibility.
2. **Step 2 — Analyze results** *(Orchestration)*: one agent combines the
   four results with the customer's goals and decides how to handle the case.
3. **Step 3 — Select path** *(Routing)*: the case is dispatched to one of the
   three resolution paths based on that decision.
4. **Step 4 — Execute resolution** *(Chaining)*: the selected chain runs its
   actions **in order** and actually updates the JSON files (e.g. append the
   refund request, decrement stock, add the replacement order). For the VIP
   premium path: approve refund → process payment immediately → create
   express replacement order → provide tracking link.
5. Finish with **one** customer-facing reply — the customer should experience
   a single smooth interaction, not four patterns.

## Hints (no code — one per step)

- **Getting IDs and goals out of the free text**: an agent call with
  `structured_output_model=` and a small Pydantic model turns
  *"...I need a refund, but I also want to reorder..."* into typed fields
  (see demo `04_structured_output.py`).
- **Step 1**: the four checks are deterministic data lookups — plain `async`
  Python functions fanned out with `asyncio.gather(...)` are enough. No LLM
  needed here.
- **Step 2**: give the orchestrator agent the routing rules in its system
  prompt and the four check results as JSON in the user prompt. Return a
  Pydantic model whose `recommended_path` field is a
  `Literal["premium", "standard", "escalation"]` — validation then guarantees
  the routing input is well-formed.
- **Step 3**: with a typed decision, routing is a dictionary lookup:
  `{"premium": premium_chain, ...}[analysis.recommended_path]`.
- **Step 4**: each chain is an ordered sequence of small functions that read,
  modify, and write the JSON files. Sequential order matters: don't process a
  payment before the refund is approved.
- **Eligibility rules** live in `data/refunds.json` → `policy`: claims are
  only valid within `max_days_since_order`; status `lost` is valid;
  `in_transit` only counts if tracking hasn't moved for
  `stuck_in_transit_days`; `delivered` contradicting the claim is suspicious;
  `refunded` is invalid.

## Stuck? Use the peek ladder — in this order

The reference solution lives in
[`../solutions/10_customer_support_tickets/`](../solutions/10_customer_support_tickets/).

1. **Compare behavior**:
   [`sample_output.md`](../solutions/10_customer_support_tickets/sample_output.md)
   shows verified transcripts for all three routes and the data mutations to
   expect — check your output against them without reading any code.
2. **Re-read the hints** above; each names the exact SDK feature to reach for.
3. **Peek at the code**:
   [`solution_code.py`](../solutions/10_customer_support_tickets/solution_code.py)
   — one file, sections labeled Step 0–4 with the pattern named at each point.

Remember: `python generate_data.py` resets the data between experiments.

## 📖 Official documentation

- [Multi-agent: Workflow](https://strandsagents.com/docs/user-guide/concepts/multi-agent/workflow/) — the workflow patterns (chaining, parallelization, orchestration, routing) this capstone combines
- [Python Tools](https://strandsagents.com/docs/user-guide/concepts/tools/python-tools/) — custom tools for the ticket/refund data operations
