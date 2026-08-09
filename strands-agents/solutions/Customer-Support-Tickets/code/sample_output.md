# Sample output — verified runs (Amazon Nova Lite)

Real transcripts from running `code/solution_code.py` against pristine data
(`python generate_data.py` before each run). Use these to check the *behavior*
of your own solution before peeking at the solution code.

The exact LLM wording (reasoning, customer reply) varies between runs — what
must match is the routing decision and the sequence of chain actions.

---

## Run 1 — Premium path (canonical scenario, default request)

```
$ python code/solution_code.py
```

```text
Customer request: "Customer C001 here about order O1001: My order never arrived, I need a refund, but I also want to reorder if you have stock."

======================================================================
STEP 0 - INTAKE  [structured output]
======================================================================
customer_id: C001
order_id:    O1001
goals:       ['refund', 'reorder']

======================================================================
STEP 1 - ASSESS SITUATION  [PATTERNS: Chaining + Parallelization]
======================================================================
Querying 4 systems simultaneously (asyncio.gather)...
  customer status:    Anna Schmidt — tier: vip
  order tracking:     status 'lost', 12 days since order
  inventory:          all items in stock: True
  refund eligibility: valid — Carrier reported the parcel as lost.

======================================================================
STEP 2 - ANALYZE RESULTS  [PATTERN: Orchestration]
======================================================================
vip_status:       True
claim_valid:      True
stock_available:  True
priority:         high
recommended_path: premium
reasoning:        The customer is a VIP and the refund claim is valid as the parcel was reported lost by the carrier. All items are available for reorder and the claim falls within the refund window. Therefore, this case should be handled with high priority and routed to the 'premium' path.

======================================================================
STEP 3 - SELECT PATH  [PATTERN: Routing]
======================================================================
Routing to the 'premium' resolution chain.

======================================================================
STEP 4 - EXECUTE RESOLUTION (premium)  [PATTERN: Chaining]
======================================================================
  1. Approve refund      -> EUR 89.99 approved
  2. Process payment     -> paid, reference PAY-O1001
  3. Offer express reorder -> replacement REO-O1001 created (express, free)
  4. Provide tracking link -> https://tracking.example.com/REO-O1001

======================================================================
CUSTOMER REPLY  (one smooth interaction)
======================================================================
Hi Anna,

Thank you for reaching out. We've processed a refund of EUR 89.99 for order O1001 and immediately completed the payment (reference PAY-O1001). Additionally, we've created a free express replacement order REO-O1001 for you. You can track it using this link: https://tracking.example.com/REO-O1001.

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

======================================================================
STEP 0 - INTAKE  [structured output]
======================================================================
customer_id: C002
order_id:    O1002
goals:       ['refund', 'replacement']

======================================================================
STEP 1 - ASSESS SITUATION  [PATTERNS: Chaining + Parallelization]
======================================================================
Querying 4 systems simultaneously (asyncio.gather)...
  customer status:    Ben Weber — tier: standard
  order tracking:     status 'lost', 10 days since order
  inventory:          all items in stock: True
  refund eligibility: valid — Carrier reported the parcel as lost.

======================================================================
STEP 2 - ANALYZE RESULTS  [PATTERN: Orchestration]
======================================================================
vip_status:       False
claim_valid:      True
stock_available:  True
priority:         normal
recommended_path: standard
reasoning:        The customer is a standard tier customer, the refund claim is valid, and the item is available for replacement. Therefore, this case should follow the standard resolution path.

======================================================================
STEP 3 - SELECT PATH  [PATTERN: Routing]
======================================================================
Routing to the 'standard' resolution chain.

======================================================================
STEP 4 - EXECUTE RESOLUTION (standard)  [PATTERN: Chaining]
======================================================================
  1. Queue refund        -> EUR 129.00 queued (3-5 business days)
  2. Offer reorder       -> items in stock, standard shipping offered
  3. Send confirmation   -> email sent

======================================================================
CUSTOMER REPLY  (one smooth interaction)
======================================================================
Hi Ben Weber,

Thank you for reaching out. We've processed a refund of EUR 129.00 for your order O1002, which will be credited within 3-5 business days. We've also offered a replacement, and your items are in stock. A confirmation email with the refund reference and next steps has been sent to you.

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

======================================================================
STEP 0 - INTAKE  [structured output]
======================================================================
customer_id: C003
order_id:    O1003
goals:       ['refund']

======================================================================
STEP 1 - ASSESS SITUATION  [PATTERNS: Chaining + Parallelization]
======================================================================
Querying 4 systems simultaneously (asyncio.gather)...
  customer status:    Clara Fischer — tier: standard
  order tracking:     status 'delivered', 8 days since order
  inventory:          all items in stock: True
  refund eligibility: suspicious — Carrier confirmed delivery; claim contradicts tracking.

======================================================================
STEP 2 - ANALYZE RESULTS  [PATTERN: Orchestration]
======================================================================
vip_status:       False
claim_valid:      False
stock_available:  True
priority:         normal
recommended_path: escalation
reasoning:        The refund claim is invalid and suspicious because the carrier confirmed delivery, which contradicts the refund claim. Additionally, the customer is not a VIP, so they do not qualify for the premium resolution path.

======================================================================
STEP 3 - SELECT PATH  [PATTERN: Routing]
======================================================================
Routing to the 'escalation' resolution chain.

======================================================================
STEP 4 - EXECUTE RESOLUTION (escalation)  [PATTERN: Chaining]
======================================================================
  1. Create review ticket -> escalated: Carrier confirmed delivery; claim contradicts tracking.
  2. Notify customer      -> manual review notice sent

======================================================================
CUSTOMER REPLY  (one smooth interaction)
======================================================================
Dear Clara Fischer,

Thank you for reaching out. Our team escalated your case for a human review, as the carrier confirmed that delivery has been made, which contradicts your report. We are now conducting a manual review to resolve this. Please rest assured we are working on it and will keep you updated.

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
