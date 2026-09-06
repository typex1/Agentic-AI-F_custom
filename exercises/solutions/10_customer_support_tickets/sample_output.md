# Sample output — verified runs (Amazon Nova Lite)

Real transcripts from running `code/solution_code.py` against pristine data
(`python generate_data.py` before each run). Use these to check the *behavior*
of your own solution before peeking at the solution code.

Every stage in the output is labeled: `>> LLM AGENT <<` means an actual agent
call (model + prompt + structured output); `[rule-based]` means plain Python
with no LLM involved. **Only 3 of the 6 stages need an agent** — the parallel
system checks, the routing dispatch, and the resolution chains are
deterministic code.

The exact LLM wording (reasoning, customer reply) varies between runs — what
must match is the routing decision and the sequence of chain actions.

---

## Run 1 — Premium path (canonical scenario, default request)

```
$ python code/solution_code.py
```

```text
Customer request: "Customer C001 here about order O1001: My order never arrived, I need a refund, but I also want to reorder if you have stock."

Legend:  >> LLM AGENT << = agent call (Nova Lite + prompt + structured output)
         [rule-based]    = plain Python, no LLM involved
Only 3 of the 6 stages below need an agent.

======================================================================
STEP 0 - INTAKE  >> LLM AGENT #1 <<  (prompt + structured output)
======================================================================
The agent turned free text into typed fields:
  customer_id: C001
  order_id:    O1001
  goals:       ['refund', 'reorder']

======================================================================
STEP 1 - ASSESS SITUATION  [rule-based]  (Chaining + Parallelization)
======================================================================
No LLM here — 4 plain Python lookups run concurrently (asyncio.gather):
  [rule-based] customer status:    Anna Schmidt — tier: vip
  [rule-based] order tracking:     status 'lost', 12 days since order
  [rule-based] inventory:          all items in stock: True
  [rule-based] refund eligibility: valid — Carrier reported the parcel as lost.

======================================================================
STEP 2 - ANALYZE RESULTS  >> LLM AGENT #2 <<  (Orchestration)
======================================================================
The agent combines the 4 results + goals and decides the path:
  vip_status:       True
  claim_valid:      True
  stock_available:  True
  priority:         high
  recommended_path: premium
  reasoning:        The customer is a VIP and the refund claim is valid, so this case should be routed to the 'premium' path.

======================================================================
STEP 3 - SELECT PATH  [rule-based]  (Routing)
======================================================================
No LLM here — the decision was already made in Step 2; this is just a
dict lookup on the validated enum -> 'premium' resolution chain.

======================================================================
STEP 4 - EXECUTE RESOLUTION (premium)  [rule-based]  (Chaining)
======================================================================
No LLM here — deterministic actions run in a fixed order, updating data/:
  1. Approve refund      -> EUR 89.99 approved
  2. Process payment     -> paid, reference PAY-O1001
  3. Offer express reorder -> replacement REO-O1001 created (express, free)
  4. Provide tracking link -> https://tracking.example.com/REO-O1001

======================================================================
CUSTOMER REPLY  >> LLM AGENT #3 <<  (one smooth interaction)
======================================================================
The agent writes the final message from the list of actions taken:

Dear Anna,

Thank you for reaching out. We've processed a refund of EUR 89.99 for your order O1001, which has been credited to your account instantly (reference PAY-O1001). Additionally, we've created an express replacement order REO-O1001 for you free of charge. You can track your new order here: https://tracking.example.com/REO-O1001.

Best regards,
Customer Support Team

Note: data/ was mutated by Step 4 — run generate_data.py to reset.
```

Data mutations after this run (check `data/`):

- `orders.json`: `O1001` status → `refunded`, new order `REO-O1001` (in_transit)
- `inventory.json`: `SKU-1001` stock 42 → 41
- `refunds.json`: refund request for `O1001`, status `paid`, reference `PAY-O1001`

---

## Run 2 — Standard path

```
$ python code/solution_code.py "Customer C002 here about order O1002: my package is lost, I want a refund and a replacement."
```

```text
Customer request: "Customer C002 here about order O1002: my package is lost, I want a refund and a replacement."

Legend:  >> LLM AGENT << = agent call (Nova Lite + prompt + structured output)
         [rule-based]    = plain Python, no LLM involved
Only 3 of the 6 stages below need an agent.

======================================================================
STEP 0 - INTAKE  >> LLM AGENT #1 <<  (prompt + structured output)
======================================================================
The agent turned free text into typed fields:
  customer_id: C002
  order_id:    O1002
  goals:       ['refund', 'replacement']

======================================================================
STEP 1 - ASSESS SITUATION  [rule-based]  (Chaining + Parallelization)
======================================================================
No LLM here — 4 plain Python lookups run concurrently (asyncio.gather):
  [rule-based] customer status:    Ben Weber — tier: standard
  [rule-based] order tracking:     status 'lost', 10 days since order
  [rule-based] inventory:          all items in stock: True
  [rule-based] refund eligibility: valid — Carrier reported the parcel as lost.

======================================================================
STEP 2 - ANALYZE RESULTS  >> LLM AGENT #2 <<  (Orchestration)
======================================================================
The agent combines the 4 results + goals and decides the path:
  vip_status:       False
  claim_valid:      True
  stock_available:  True
  priority:         normal
  recommended_path: standard
  reasoning:        The customer is a standard tier, the parcel was lost, the item is in stock, and the refund claim is valid. The customer is within the refund window.

======================================================================
STEP 3 - SELECT PATH  [rule-based]  (Routing)
======================================================================
No LLM here — the decision was already made in Step 2; this is just a
dict lookup on the validated enum -> 'standard' resolution chain.

======================================================================
STEP 4 - EXECUTE RESOLUTION (standard)  [rule-based]  (Chaining)
======================================================================
No LLM here — deterministic actions run in a fixed order, updating data/:
  1. Queue refund        -> EUR 129.00 queued (3-5 business days)
  2. Offer reorder       -> items in stock, standard shipping offered
  3. Send confirmation   -> email sent

======================================================================
CUSTOMER REPLY  >> LLM AGENT #3 <<  (one smooth interaction)
======================================================================
The agent writes the final message from the list of actions taken:

Dear Ben Weber,

Thank you for reaching out. We have processed a refund of EUR 129.00 for your order O1002, which will be completed in 3-5 business days. Additionally, we have offered a replacement order for your lost items, which are currently in stock and will be shipped at standard rates. A confirmation email with the refund reference and next steps has been sent to you.

Best regards,
Customer Support Team

Note: data/ was mutated by Step 4 — run generate_data.py to reset.
```

---

## Run 3 — Escalation path (suspicious claim)

```
$ python code/solution_code.py "Customer C003, order O1003: my order never arrived, refund me."
```

```text
Customer request: "Customer C003, order O1003: my order never arrived, refund me."

Legend:  >> LLM AGENT << = agent call (Nova Lite + prompt + structured output)
         [rule-based]    = plain Python, no LLM involved
Only 3 of the 6 stages below need an agent.

======================================================================
STEP 0 - INTAKE  >> LLM AGENT #1 <<  (prompt + structured output)
======================================================================
The agent turned free text into typed fields:
  customer_id: C003
  order_id:    O1003
  goals:       ['order not received', 'refund']

======================================================================
STEP 1 - ASSESS SITUATION  [rule-based]  (Chaining + Parallelization)
======================================================================
No LLM here — 4 plain Python lookups run concurrently (asyncio.gather):
  [rule-based] customer status:    Clara Fischer — tier: standard
  [rule-based] order tracking:     status 'delivered', 8 days since order
  [rule-based] inventory:          all items in stock: True
  [rule-based] refund eligibility: suspicious — Carrier confirmed delivery; claim contradicts tracking.

======================================================================
STEP 2 - ANALYZE RESULTS  >> LLM AGENT #2 <<  (Orchestration)
======================================================================
The agent combines the 4 results + goals and decides the path:
  vip_status:       False
  claim_valid:      False
  stock_available:  True
  priority:         normal
  recommended_path: escalation
  reasoning:        The customer's claim that the order was not received is contradicted by the carrier's confirmation of delivery. The refund claim is marked as invalid and suspicious, so this case should be escalated for a human review.

======================================================================
STEP 3 - SELECT PATH  [rule-based]  (Routing)
======================================================================
No LLM here — the decision was already made in Step 2; this is just a
dict lookup on the validated enum -> 'escalation' resolution chain.

======================================================================
STEP 4 - EXECUTE RESOLUTION (escalation)  [rule-based]  (Chaining)
======================================================================
No LLM here — deterministic actions run in a fixed order, updating data/:
  1. Create review ticket -> escalated: Carrier confirmed delivery; claim contradicts tracking.
  2. Notify customer      -> manual review notice sent

======================================================================
CUSTOMER REPLY  >> LLM AGENT #3 <<  (one smooth interaction)
======================================================================
The agent writes the final message from the list of actions taken:

Hi Clara,

Thank you for reaching out. We escalated your case (order O1003) to a human review. The carrier confirmed that your order was delivered, which contradicts your claim of non-delivery. We've notified you that the case requires manual review, and an automatic refund isn't possible at this stage.

Best regards,
Customer Support Team

Note: data/ was mutated by Step 4 — run generate_data.py to reset.
```

---

## Bonus — Premium path, out-of-stock variant

`O1004` (VIP customer C004, item out of stock) also routes to **premium**, but
the chain takes the refund-only branch:

```text
  1. Approve refund      -> EUR 398.00 approved
  2. Process payment     -> paid, reference PAY-O1004
  3. Offer express reorder -> OUT OF STOCK, restock expected 2026-08-30
  4. Provide tracking link -> skipped (no replacement order)
```

(The restock date is generated relative to "today" — yours will differ.)

---

## Other scenarios to try

| Request about | Expected route | Why |
|---|---|---|
| C005 / O1005 | standard | in_transit with no movement for 14 days → stuck → valid claim |
| C006 / O1006 | escalation | already refunded → invalid claim |
| C008 / O1008 | escalation | 45 days old → outside the 30-day refund window |
