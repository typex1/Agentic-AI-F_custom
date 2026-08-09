# Reference solution — end-to-end flow

How [`solution_code.py`](solution_code.py) resolves a support ticket, and where
each of the four agent workflow patterns lives. LLM steps run on Amazon Nova
Lite (`amazon.nova-lite-v1:0`); everything else is plain Python.

```mermaid
flowchart TD
    REQ(["Customer request<br/>(free text, CLI arg)"])

    subgraph S0["STEP 0 — Intake"]
        INTAKE["Intake agent · LLM<br/>structured output → IntakeResult:<br/>customer_id, order_id, goals[]"]
    end

    subgraph S1["STEP 1 — Assess situation · CHAINING + PARALLELIZATION"]
        FAN{{"asyncio.gather — fan-out"}}
        CRM["check_customer_status<br/>CRM · customers.json"]
        TRK["check_order_tracking<br/>Orders · orders.json"]
        INV["check_inventory<br/>Warehouse · inventory.json"]
        REF["check_refund_eligibility<br/>Billing · refunds.json"]
        JOIN{{"fan-in — 4 results combined"}}
    end

    subgraph S2["STEP 2 — Analyze results · ORCHESTRATION"]
        ORCH["Orchestrator agent · LLM<br/>structured output → SituationAnalysis:<br/>vip_status, claim_valid, stock_available,<br/>priority, recommended_path"]
    end

    subgraph S3["STEP 3 — Select path · ROUTING"]
        ROUTE{"recommended_path?<br/>(validated Literal enum,<br/>dict dispatch)"}
    end

    subgraph S4["STEP 4 — Execute resolution · CHAINING"]
        subgraph PREM["premium chain — VIP"]
            direction TB
            P1["1 · Approve refund"] --> P2["2 · Process payment<br/>immediately"]
            P2 --> P3["3 · Offer express reorder<br/>(if stock, else restock ETA)"]
            P3 --> P4["4 · Provide tracking link"]
        end
        subgraph STD["standard chain"]
            direction TB
            T1["1 · Queue refund<br/>(3–5 business days)"] --> T2["2 · Offer standard reorder"]
            T2 --> T3["3 · Send confirmation"]
        end
        subgraph ESC["escalation chain"]
            direction TB
            E1["1 · Create human-review<br/>ticket"] --> E2["2 · Notify customer"]
        end
    end

    REPLY["Reply agent · LLM<br/>ONE smooth customer-facing message"]
    DATA[("data/*.json mutated<br/>reset: generate_data.py")]

    REQ --> INTAKE
    INTAKE --> FAN
    FAN --> CRM & TRK & INV & REF
    CRM --> JOIN
    TRK --> JOIN
    INV --> JOIN
    REF --> JOIN
    JOIN --> ORCH
    ORCH --> ROUTE
    ROUTE -- "VIP + valid claim" --> PREM
    ROUTE -- "valid claim, not VIP" --> STD
    ROUTE -- "invalid / suspicious claim" --> ESC
    PREM --> REPLY
    STD --> REPLY
    ESC --> REPLY
    S4 -.writes.-> DATA
```

## Pattern-to-step map

| Pattern | Where | How it shows up in the code |
|---|---|---|
| **Chaining** | backbone + Step 4 | `run_workflow()` runs Steps 0→4 in order; each resolution chain is an ordered sequence of actions (payment never before refund approval) |
| **Parallelization** | inside Step 1 | four independent system checks fanned out with `asyncio.gather`, joined into one assessment |
| **Orchestration** | Step 2 | one agent combines all four results with the customer's goals and produces a typed decision (`SituationAnalysis`) |
| **Routing** | Step 3 | dispatch on the LLM-chosen `recommended_path` enum — a different request takes a different chain |

The three LLM calls (intake, orchestrator, reply) all use Pydantic structured
output or a tight prompt; the deterministic work (lookups, branching, data
mutation) stays in plain Python. Verified transcripts for all three routes:
[`sample_output.md`](sample_output.md).
