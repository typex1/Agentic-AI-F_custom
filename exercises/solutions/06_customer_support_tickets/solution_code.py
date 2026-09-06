"""
solution_code.py — Customer support ticket resolution (reference solution)

Implements the four-pattern workflow from the slide / README:

  Step 0  INTAKE            LLM + structured output: extract IDs and goals
  Step 1  ASSESS SITUATION  [Chaining + PARALLELIZATION] four systems queried
                            simultaneously via asyncio.gather
  Step 2  ANALYZE RESULTS   [ORCHESTRATION] one agent combines all four
                            results and decides the resolution path
  Step 3  SELECT PATH       [ROUTING] dispatch on the agent's typed decision
  Step 4  EXECUTE           [CHAINING] the selected resolution chain runs
                            its steps in order and mutates the data files

Run (canonical VIP scenario — premium path):
  python solution_code.py

Run with your own request (routing will diverge based on the data):
  python solution_code.py "Customer C002 here about order O1002: my package is lost, I want a refund and a replacement."
  python solution_code.py "Customer C003, order O1003: my order never arrived, refund me."

Reset the data after runs (Step 4 mutates the JSON files):
  python ../generate_data.py
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import asyncio
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from strands import Agent
from strands.models import BedrockModel

# Data lives in the task's data folder (exercises/tasks/06_customer_support_tickets_data/)
# so students build their own solution against the same files.
DATA_DIR = Path(__file__).parent.parent.parent / "tasks" / "06_customer_support_tickets_data" / "data"

MODEL_ID = "amazon.nova-lite-v1:0"  # the only model permitted in this environment
AWS_REGION = "us-east-1"


def _model() -> BedrockModel:
    # temperature=0 keeps the intake extraction and the routing decision
    # reproducible — important for a workflow that dispatches on LLM output.
    return BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.0)

CANONICAL_REQUEST = (
    "Customer C001 here about order O1001: My order never arrived, I need a "
    "refund, but I also want to reorder if you have stock."
)


# ---------------------------------------------------------------------------
# Small helpers for the mock backend "systems" (four JSON files)
# ---------------------------------------------------------------------------

def _load(name: str):
    return json.loads((DATA_DIR / name).read_text())


def _save(name: str, payload) -> None:
    (DATA_DIR / name).write_text(json.dumps(payload, indent=2) + "\n")


def banner(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


# ===========================================================================
# STEP 0 — INTAKE (LLM + structured output)
#
# The orchestration idea starts here: before anything runs, we turn the
# free-text customer request into typed data — who is asking, which order,
# and the LIST OF GOALS (a single message can carry several goals, e.g.
# refund + reorder). The plan for the rest of the workflow hangs off this.
# ===========================================================================

class IntakeResult(BaseModel):
    """Typed extraction of the customer's free-text request."""
    customer_id: str = Field(description="Customer ID mentioned in the request, e.g. C001")
    order_id: str = Field(description="Order ID mentioned in the request, e.g. O1001")
    goals: list[str] = Field(description="Each distinct goal of the customer, e.g. 'refund', 'reorder', 'delivery status'")


def intake(request: str) -> IntakeResult:
    agent = Agent(
        model=_model(),
        system_prompt=(
            "You are the intake step of a customer support workflow. "
            "Extract the customer ID, the order ID, and every distinct goal "
            "from the customer's message. Do not invent IDs."
        ),
        callback_handler=None,  # no streaming; we print the structured result
    )
    result = agent(request, structured_output_model=IntakeResult)
    return result.structured_output


# ===========================================================================
# STEP 1 — ASSESS SITUATION            [PATTERN: Chaining + PARALLELIZATION]
#
# One step of the overall chain — but INSIDE it, four independent backend
# systems are queried simultaneously with asyncio.gather. The four checks
# are plain async functions (deterministic data lookups need no LLM; in a
# real system they would be API calls, and a stronger model could even
# emit the four tool calls itself — "model-driven" parallelization).
# ===========================================================================

async def check_customer_status(customer_id: str) -> dict:
    """System 1 — CRM: who is this customer, what support tier?"""
    for c in _load("customers.json"):
        if c["customer_id"] == customer_id:
            return {"found": True, **c}
    return {"found": False, "customer_id": customer_id}


async def check_order_tracking(order_id: str) -> dict:
    """System 2 — Order management: order status + tracking history."""
    for o in _load("orders.json"):
        if o["order_id"] == order_id:
            days = (date.today() - date.fromisoformat(o["order_date"])).days
            return {"found": True, "days_since_order": days, **o}
    return {"found": False, "order_id": order_id}


async def check_inventory(order_id: str) -> dict:
    """System 3 — Warehouse: are the ordered items in stock for a reorder?"""
    order = next((o for o in _load("orders.json") if o["order_id"] == order_id), None)
    if order is None:
        return {"found": False, "order_id": order_id}
    inventory = {i["sku"]: i for i in _load("inventory.json")}
    items = []
    for item in order["items"]:
        inv = inventory.get(item["sku"], {})
        items.append({
            "sku": item["sku"],
            "product_name": inv.get("product_name", "unknown"),
            "quantity_needed": item["quantity"],
            "units_in_stock": inv.get("units_in_stock", 0),
            "in_stock": inv.get("units_in_stock", 0) >= item["quantity"],
            "restock_eta": inv.get("restock_eta"),
        })
    return {"found": True, "all_items_in_stock": all(i["in_stock"] for i in items), "items": items}


async def check_refund_eligibility(order_id: str) -> dict:
    """System 4 — Billing: is a refund claim for this order valid per policy?"""
    order = next((o for o in _load("orders.json") if o["order_id"] == order_id), None)
    if order is None:
        return {"found": False, "order_id": order_id}
    policy = _load("refunds.json")["policy"]
    days_since_order = (date.today() - date.fromisoformat(order["order_date"])).days
    status = order["status"]

    if status == "refunded":
        assessment, reason = "invalid", "Order was already refunded."
    elif days_since_order > policy["max_days_since_order"]:
        assessment, reason = "invalid", (
            f"Order is {days_since_order} days old — outside the "
            f"{policy['max_days_since_order']}-day refund window."
        )
    elif status == "delivered":
        assessment, reason = "suspicious", "Carrier confirmed delivery; claim contradicts tracking."
    elif status == "lost":
        assessment, reason = "valid", "Carrier reported the parcel as lost."
    else:  # in_transit — valid only if the parcel has stopped moving
        last_event = max(e["timestamp"] for e in order["tracking_events"])
        days_stuck = (datetime.now() - datetime.fromisoformat(last_event)).days
        if days_stuck >= policy["stuck_in_transit_days"]:
            assessment, reason = "valid", f"No tracking movement for {days_stuck} days (stuck in transit)."
        else:
            assessment, reason = "invalid", f"Parcel is still moving (last event {days_stuck} days ago)."

    return {
        "found": True,
        "claim_valid": assessment == "valid",
        "assessment": assessment,   # valid | invalid | suspicious
        "reason": reason,
        "days_since_order": days_since_order,
        "policy": policy,
    }


async def assess_situation(customer_id: str, order_id: str) -> dict:
    # PARALLELIZATION: all four system checks run concurrently.
    customer, tracking, inventory, refund = await asyncio.gather(
        check_customer_status(customer_id),
        check_order_tracking(order_id),
        check_inventory(order_id),
        check_refund_eligibility(order_id),
    )
    return {
        "customer_status": customer,
        "order_tracking": tracking,
        "inventory": inventory,
        "refund_eligibility": refund,
    }


# ===========================================================================
# STEP 2 — ANALYZE RESULTS                          [PATTERN: ORCHESTRATION]
#
# A single agent combines the four parallel results, weighs them against
# the customer's goals, and produces a TYPED decision — including the
# resolution path. The LLM makes the dynamic decision; the structured
# output schema (Pydantic) keeps the handoff to routing safe.
# ===========================================================================

class SituationAnalysis(BaseModel):
    """The orchestrator's combined analysis of all four system checks."""
    vip_status: bool = Field(description="Is the customer a VIP-tier customer?")
    claim_valid: bool = Field(description="Is the refund claim valid per the eligibility check?")
    stock_available: bool = Field(description="Are all ordered items in stock for a reorder?")
    priority: Literal["high", "normal"] = Field(description="Case priority")
    recommended_path: Literal["premium", "standard", "escalation"] = Field(
        description="Which resolution path to route this case to"
    )
    reasoning: str = Field(description="One short paragraph explaining the decision")


def analyze_results(goals: list[str], assessment: dict) -> SituationAnalysis:
    agent = Agent(
        model=_model(),
        system_prompt=(
            "You are the orchestrator of a customer support workflow. You are "
            "given the customer's goals and the results of four parallel "
            "system checks. Combine them and decide the resolution path.\n"
            "Routing rules:\n"
            "- 'premium': the refund claim is valid (claim_valid true) AND the "
            "customer tier is 'vip'. High priority.\n"
            "- 'standard': the refund claim is valid but the customer is not VIP.\n"
            "- 'escalation': the claim is invalid or suspicious (e.g. carrier "
            "confirmed delivery, already refunded, outside the refund window). "
            "A human must review it.\n"
            "Base every field strictly on the provided data."
        ),
        callback_handler=None,
    )
    prompt = (
        f"Customer goals: {goals}\n\n"
        f"Results of the four parallel system checks:\n"
        f"{json.dumps(assessment, indent=2)}"
    )
    result = agent(prompt, structured_output_model=SituationAnalysis)
    return result.structured_output


# ===========================================================================
# STEP 4 — EXECUTE RESOLUTION                            [PATTERN: CHAINING]
#
# Three alternative chains. Each is a plain ordered sequence of actions —
# sequential execution ensures the correct order (a payment must not run
# before its refund is approved). The actions really mutate the JSON
# files; rerun generate_data.py to reset.
# ===========================================================================

def _order_amount(order: dict) -> float:
    return round(sum(i["quantity"] * i["unit_price"] for i in order["items"]), 2)


def _append_refund_request(order: dict, status: str, note: str) -> dict:
    refunds = _load("refunds.json")
    entry = {
        "order_id": order["order_id"],
        "customer_id": order["customer_id"],
        "amount": _order_amount(order),
        "status": status,
        "note": note,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    refunds["refund_requests"].append(entry)
    _save("refunds.json", refunds)
    return entry


def _set_order_status(order_id: str, status: str) -> None:
    orders = _load("orders.json")
    for o in orders:
        if o["order_id"] == order_id:
            o["status"] = status
    _save("orders.json", orders)


def premium_chain(order: dict, assessment: dict) -> list[str]:
    """VIP resolution chain — exactly the four steps from the slide."""
    actions = []

    # 1. Approve refund
    entry = _append_refund_request(order, "approved", "VIP premium path: instant approval")
    _set_order_status(order["order_id"], "refunded")
    actions.append(f"Refund of EUR {entry['amount']:.2f} approved instantly (VIP).")
    print(f"  1. Approve refund      -> EUR {entry['amount']:.2f} approved")

    # 2. Process payment immediately
    refunds = _load("refunds.json")
    refunds["refund_requests"][-1]["status"] = "paid"
    refunds["refund_requests"][-1]["payment_reference"] = f"PAY-{order['order_id']}"
    _save("refunds.json", refunds)
    actions.append("Payment processed immediately (reference PAY-" + order["order_id"] + ").")
    print(f"  2. Process payment     -> paid, reference PAY-{order['order_id']}")

    # 3. Offer express reorder (only if stock is available)
    if assessment["inventory"]["all_items_in_stock"]:
        inventory = _load("inventory.json")
        for item in order["items"]:
            for inv in inventory:
                if inv["sku"] == item["sku"]:
                    inv["units_in_stock"] -= item["quantity"]
        _save("inventory.json", inventory)

        reorder_id = f"REO-{order['order_id']}"
        orders = _load("orders.json")
        orders.append({
            "order_id": reorder_id,
            "customer_id": order["customer_id"],
            "order_date": date.today().isoformat(),
            "status": "in_transit",
            "items": order["items"],
            "tracking_events": [
                {"timestamp": datetime.now().isoformat(timespec="seconds"),
                 "event": "Express replacement order created (free of charge)"},
            ],
        })
        _save("orders.json", orders)
        actions.append(f"Express replacement order {reorder_id} created free of charge.")
        print(f"  3. Offer express reorder -> replacement {reorder_id} created (express, free)")

        # 4. Provide tracking link
        link = f"https://tracking.example.com/{reorder_id}"
        actions.append(f"Tracking link for the replacement: {link}")
        print(f"  4. Provide tracking link -> {link}")
    else:
        etas = [i["restock_eta"] for i in assessment["inventory"]["items"] if not i["in_stock"]]
        actions.append(f"Reorder not possible: item(s) out of stock, restock expected {etas[0]}.")
        print(f"  3. Offer express reorder -> OUT OF STOCK, restock expected {etas[0]}")
        actions.append("VIP will be notified with priority as soon as stock arrives.")
        print("  4. Provide tracking link -> skipped (no replacement order)")

    return actions


def standard_chain(order: dict, assessment: dict) -> list[str]:
    """Standard resolution chain — refund via the normal queue."""
    actions = []

    entry = _append_refund_request(order, "queued", "Standard path: normal refund queue")
    _set_order_status(order["order_id"], "refund_pending")
    actions.append(f"Refund of EUR {entry['amount']:.2f} queued (processing in 3-5 business days).")
    print(f"  1. Queue refund        -> EUR {entry['amount']:.2f} queued (3-5 business days)")

    if assessment["inventory"]["all_items_in_stock"]:
        actions.append("Items are in stock: replacement order offered at standard shipping.")
        print("  2. Offer reorder       -> items in stock, standard shipping offered")
    else:
        actions.append("Items currently out of stock; customer informed of restock ETA.")
        print("  2. Offer reorder       -> out of stock, ETA communicated")

    actions.append("Confirmation email sent with refund reference and next steps.")
    print("  3. Send confirmation   -> email sent")
    return actions


def escalation_chain(order: dict, assessment: dict) -> list[str]:
    """Escalation chain — claim invalid or suspicious, a human takes over."""
    actions = []
    reason = assessment["refund_eligibility"]["reason"]

    entry = _append_refund_request(order, "escalated_to_human_review", reason)
    actions.append(f"Case escalated to human review (ticket for order {order['order_id']}): {reason}")
    print(f"  1. Create review ticket -> escalated: {reason}")

    actions.append("Customer notified that the case needs manual review (no automatic refund).")
    print("  2. Notify customer      -> manual review notice sent")
    return actions


# ===========================================================================
# STEP 3 — SELECT PATH                                    [PATTERN: ROUTING]
#
# The orchestrator (Step 2) already made the dynamic decision; here the
# code dispatches on the validated enum. (A deterministic alternative
# would be a hard-coded if/else on vip_status and claim_valid.)
# ===========================================================================

RESOLUTION_CHAINS = {
    "premium": premium_chain,
    "standard": standard_chain,
    "escalation": escalation_chain,
}


# ===========================================================================
# Final touch — compose the one smooth customer-facing reply.
# The customer experiences ONE interaction; the four patterns stay invisible.
# ===========================================================================

def compose_reply(request: str, customer: dict, actions: list[str]) -> str:
    agent = Agent(
        model=_model(),
        system_prompt=(
            "You are a customer support agent writing the final reply. "
            "Write a short, friendly message (max 120 words) to the customer "
            "summarizing ONLY the actions that were actually taken. "
            "Address the customer by name. Do not invent actions."
        ),
        callback_handler=None,
    )
    prompt = (
        f"Customer name: {customer.get('name', 'customer')}\n"
        f"Original request: {request}\n"
        f"Actions taken:\n" + "\n".join(f"- {a}" for a in actions)
    )
    return str(agent(prompt)).strip()


# ---------------------------------------------------------------------------
# The workflow: one chain from intake to reply (CHAINING is the backbone)
# ---------------------------------------------------------------------------

async def run_workflow(request: str) -> None:
    print(f'\nCustomer request: "{request}"')
    print(
        "\nLegend:  >> LLM AGENT << = agent call (Nova Lite + prompt + structured output)"
        "\n         [rule-based]    = plain Python, no LLM involved"
        "\nOnly 3 of the 6 stages below need an agent."
    )

    banner("STEP 0 - INTAKE  >> LLM AGENT #1 <<  (prompt + structured output)")
    ticket = intake(request)
    print("The agent turned free text into typed fields:")
    print(f"  customer_id: {ticket.customer_id}")
    print(f"  order_id:    {ticket.order_id}")
    print(f"  goals:       {ticket.goals}")

    banner("STEP 1 - ASSESS SITUATION  [rule-based]  (Chaining + Parallelization)")
    print("No LLM here — 4 plain Python lookups run concurrently (asyncio.gather):")
    assessment = await assess_situation(ticket.customer_id, ticket.order_id)
    cust = assessment["customer_status"]
    trk = assessment["order_tracking"]
    inv = assessment["inventory"]
    ref = assessment["refund_eligibility"]
    print(f"  [rule-based] customer status:    {cust.get('name', '?')} — tier: {cust.get('tier', '?')}")
    print(f"  [rule-based] order tracking:     status '{trk.get('status', '?')}', "
          f"{trk.get('days_since_order', '?')} days since order")
    print(f"  [rule-based] inventory:          all items in stock: {inv.get('all_items_in_stock')}")
    print(f"  [rule-based] refund eligibility: {ref.get('assessment')} — {ref.get('reason')}")

    if not (cust.get("found") and trk.get("found")):
        print("\nCustomer or order not found — cannot proceed. Check the IDs.")
        return

    banner("STEP 2 - ANALYZE RESULTS  >> LLM AGENT #2 <<  (Orchestration)")
    print("The agent combines the 4 results + goals and decides the path:")
    analysis = analyze_results(ticket.goals, assessment)
    print(f"  vip_status:       {analysis.vip_status}")
    print(f"  claim_valid:      {analysis.claim_valid}")
    print(f"  stock_available:  {analysis.stock_available}")
    print(f"  priority:         {analysis.priority}")
    print(f"  recommended_path: {analysis.recommended_path}")
    print(f"  reasoning:        {analysis.reasoning}")

    banner("STEP 3 - SELECT PATH  [rule-based]  (Routing)")
    chain = RESOLUTION_CHAINS[analysis.recommended_path]  # dispatch on typed enum
    print("No LLM here — the decision was already made in Step 2; this is just a")
    print(f"dict lookup on the validated enum -> '{analysis.recommended_path}' resolution chain.")

    banner(f"STEP 4 - EXECUTE RESOLUTION ({analysis.recommended_path})  [rule-based]  (Chaining)")
    print("No LLM here — deterministic actions run in a fixed order, updating data/:")
    order = next(o for o in _load("orders.json") if o["order_id"] == ticket.order_id)
    actions = chain(order, assessment)

    banner("CUSTOMER REPLY  >> LLM AGENT #3 <<  (one smooth interaction)")
    print("The agent writes the final message from the list of actions taken:\n")
    print(compose_reply(request, cust, actions))

    print("\nNote: data/ was mutated by Step 4 — run generate_data.py to reset.")


# Going further: this pipeline is plain Python for maximum legibility.
# For a production-style, framework-managed version of the same topology
# (nodes + conditional edges), see the course sample
# sample-building-with-strands-course/samples_adjusted/11-graphs.

def main() -> None:
    request = sys.argv[1] if len(sys.argv) > 1 else CANONICAL_REQUEST
    asyncio.run(run_workflow(request))


if __name__ == "__main__":
    main()
