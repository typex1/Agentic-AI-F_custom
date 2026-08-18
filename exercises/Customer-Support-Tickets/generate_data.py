"""
generate_data.py — Synthetic data for the Customer-Support-Tickets exercise

Creates (or RESETS) the data/ folder with four JSON files, one per mock
backend system:

  data/customers.json   — CRM: customer profiles and support tier
  data/orders.json      — Order management: orders + tracking events
  data/inventory.json   — Warehouse: stock levels per SKU
  data/refunds.json     — Billing: refund policy + refund request history

Running this script again restores the pristine state (it overwrites any
mutations made by a solution run). Order dates are written relative to
"today" so the refund-policy time window always behaves the same.

Run:
  python generate_data.py

The dataset intentionally covers every routing outcome:
  O1001  VIP, lost, item in stock            -> premium path (canonical demo)
  O1002  standard, lost                      -> standard path
  O1003  carrier-confirmed delivered          -> escalation (suspicious claim)
  O1004  VIP, lost, item OUT of stock        -> premium path, refund-only variant
  O1005  standard, stuck in transit          -> standard path
  O1006  already refunded                    -> escalation (invalid claim)
  O1008  lost, but outside policy window     -> escalation (out of policy)
"""

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def days_ago(n: int) -> str:
    """ISO date n days before today."""
    return (date.today() - timedelta(days=n)).isoformat()


def ts_days_ago(n: int, hour: int = 10) -> str:
    """ISO timestamp n days before today."""
    return datetime.combine(date.today() - timedelta(days=n), time(hour)).isoformat()


CUSTOMERS = [
    {"customer_id": "C001", "name": "Anna Schmidt",   "tier": "vip",      "email": "anna.schmidt@example.com",   "customer_since": "2019-03-12"},
    {"customer_id": "C002", "name": "Ben Weber",      "tier": "standard", "email": "ben.weber@example.com",      "customer_since": "2023-07-01"},
    {"customer_id": "C003", "name": "Clara Fischer",  "tier": "standard", "email": "clara.fischer@example.com",  "customer_since": "2024-01-20"},
    {"customer_id": "C004", "name": "David Meyer",    "tier": "vip",      "email": "david.meyer@example.com",    "customer_since": "2018-11-05"},
    {"customer_id": "C005", "name": "Emma Wagner",    "tier": "standard", "email": "emma.wagner@example.com",    "customer_since": "2022-05-14"},
    {"customer_id": "C006", "name": "Felix Becker",   "tier": "standard", "email": "felix.becker@example.com",   "customer_since": "2021-09-30"},
    {"customer_id": "C007", "name": "Greta Hoffmann", "tier": "standard", "email": "greta.hoffmann@example.com", "customer_since": "2020-02-17"},
    {"customer_id": "C008", "name": "Henry Koch",     "tier": "standard", "email": "henry.koch@example.com",     "customer_since": "2024-06-08"},
]

INVENTORY = [
    {"sku": "SKU-1001", "product_name": "Wireless Headphones",      "units_in_stock": 42, "restock_eta": None},
    {"sku": "SKU-1002", "product_name": "Mechanical Keyboard",      "units_in_stock": 15, "restock_eta": None},
    {"sku": "SKU-1003", "product_name": "4K Webcam",                "units_in_stock": 0,  "restock_eta": days_ago(-21)},
    {"sku": "SKU-1004", "product_name": "USB-C Docking Station",    "units_in_stock": 27, "restock_eta": None},
    {"sku": "SKU-1005", "product_name": "Ergonomic Mouse",          "units_in_stock": 63, "restock_eta": None},
    {"sku": "SKU-1006", "product_name": "27-inch Monitor",          "units_in_stock": 8,  "restock_eta": None},
    {"sku": "SKU-1007", "product_name": "Laptop Stand",             "units_in_stock": 0,  "restock_eta": days_ago(-14)},
    {"sku": "SKU-1008", "product_name": "Noise-Cancelling Earbuds", "units_in_stock": 31, "restock_eta": None},
]

ORDERS = [
    {   # Canonical demo: VIP + lost + in stock -> premium path
        "order_id": "O1001", "customer_id": "C001", "order_date": days_ago(12), "status": "lost",
        "items": [{"sku": "SKU-1001", "quantity": 1, "unit_price": 89.99}],
        "tracking_events": [
            {"timestamp": ts_days_ago(12), "event": "Order placed"},
            {"timestamp": ts_days_ago(11), "event": "Shipped from warehouse"},
            {"timestamp": ts_days_ago(9),  "event": "Arrived at sorting facility"},
            {"timestamp": ts_days_ago(6),  "event": "Carrier reported parcel missing"},
        ],
    },
    {   # Standard customer + lost -> standard path
        "order_id": "O1002", "customer_id": "C002", "order_date": days_ago(10), "status": "lost",
        "items": [{"sku": "SKU-1002", "quantity": 1, "unit_price": 129.00}],
        "tracking_events": [
            {"timestamp": ts_days_ago(10), "event": "Order placed"},
            {"timestamp": ts_days_ago(9),  "event": "Shipped from warehouse"},
            {"timestamp": ts_days_ago(5),  "event": "Carrier reported parcel missing"},
        ],
    },
    {   # Carrier-confirmed delivery -> suspicious claim -> escalation path
        "order_id": "O1003", "customer_id": "C003", "order_date": days_ago(8), "status": "delivered",
        "items": [{"sku": "SKU-1005", "quantity": 2, "unit_price": 45.50}],
        "tracking_events": [
            {"timestamp": ts_days_ago(8), "event": "Order placed"},
            {"timestamp": ts_days_ago(7), "event": "Shipped from warehouse"},
            {"timestamp": ts_days_ago(5), "event": "Delivered — signature confirmed by carrier"},
        ],
    },
    {   # VIP + lost + item OUT of stock -> premium path, refund-only variant
        "order_id": "O1004", "customer_id": "C004", "order_date": days_ago(15), "status": "lost",
        "items": [{"sku": "SKU-1003", "quantity": 2, "unit_price": 199.00}],
        "tracking_events": [
            {"timestamp": ts_days_ago(15), "event": "Order placed"},
            {"timestamp": ts_days_ago(14), "event": "Shipped from warehouse"},
            {"timestamp": ts_days_ago(10), "event": "Carrier reported parcel missing"},
        ],
    },
    {   # Stuck in transit (no movement for 14 days) -> valid claim, standard path
        "order_id": "O1005", "customer_id": "C005", "order_date": days_ago(20), "status": "in_transit",
        "items": [{"sku": "SKU-1006", "quantity": 1, "unit_price": 279.99}],
        "tracking_events": [
            {"timestamp": ts_days_ago(20), "event": "Order placed"},
            {"timestamp": ts_days_ago(19), "event": "Shipped from warehouse"},
            {"timestamp": ts_days_ago(14), "event": "Arrived at sorting facility"},
        ],
    },
    {   # Already refunded -> invalid claim -> escalation path
        "order_id": "O1006", "customer_id": "C006", "order_date": days_ago(25), "status": "refunded",
        "items": [{"sku": "SKU-1008", "quantity": 1, "unit_price": 149.00}],
        "tracking_events": [
            {"timestamp": ts_days_ago(25), "event": "Order placed"},
            {"timestamp": ts_days_ago(24), "event": "Shipped from warehouse"},
            {"timestamp": ts_days_ago(20), "event": "Carrier reported parcel missing"},
            {"timestamp": ts_days_ago(18), "event": "Refund processed"},
        ],
    },
    {   # Normal delivered order (happy path, no claim expected)
        "order_id": "O1007", "customer_id": "C007", "order_date": days_ago(5), "status": "delivered",
        "items": [{"sku": "SKU-1004", "quantity": 1, "unit_price": 159.00}],
        "tracking_events": [
            {"timestamp": ts_days_ago(5), "event": "Order placed"},
            {"timestamp": ts_days_ago(4), "event": "Shipped from warehouse"},
            {"timestamp": ts_days_ago(2), "event": "Delivered"},
        ],
    },
    {   # Lost, but ordered 45 days ago -> outside 30-day policy window -> escalation
        "order_id": "O1008", "customer_id": "C008", "order_date": days_ago(45), "status": "lost",
        "items": [{"sku": "SKU-1007", "quantity": 1, "unit_price": 39.99}],
        "tracking_events": [
            {"timestamp": ts_days_ago(45), "event": "Order placed"},
            {"timestamp": ts_days_ago(44), "event": "Shipped from warehouse"},
            {"timestamp": ts_days_ago(40), "event": "Carrier reported parcel missing"},
        ],
    },
    {   # Recent order still moving normally (no claim expected)
        "order_id": "O1009", "customer_id": "C001", "order_date": days_ago(2), "status": "in_transit",
        "items": [{"sku": "SKU-1005", "quantity": 1, "unit_price": 45.50}],
        "tracking_events": [
            {"timestamp": ts_days_ago(2), "event": "Order placed"},
            {"timestamp": ts_days_ago(1), "event": "Shipped from warehouse"},
        ],
    },
    {   # Old delivered order (no claim expected)
        "order_id": "O1010", "customer_id": "C002", "order_date": days_ago(30), "status": "delivered",
        "items": [{"sku": "SKU-1001", "quantity": 2, "unit_price": 89.99}],
        "tracking_events": [
            {"timestamp": ts_days_ago(30), "event": "Order placed"},
            {"timestamp": ts_days_ago(29), "event": "Shipped from warehouse"},
            {"timestamp": ts_days_ago(27), "event": "Delivered"},
        ],
    },
]

REFUNDS = {
    "policy": {
        # A refund claim is only valid within this many days of the order date.
        "max_days_since_order": 30,
        # Order statuses for which a refund claim can be valid.
        "refundable_statuses": ["lost", "in_transit"],
        # An in_transit order counts as "stuck" (claim valid) if the last
        # tracking event is at least this many days old.
        "stuck_in_transit_days": 10,
    },
    # Step 4 of the workflow appends refund requests here.
    "refund_requests": [],
}


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    files = {
        "customers.json": CUSTOMERS,
        "orders.json": ORDERS,
        "inventory.json": INVENTORY,
        "refunds.json": REFUNDS,
    }
    for name, payload in files.items():
        path = DATA_DIR / name
        path.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"wrote {path.relative_to(Path(__file__).parent)}")
    print("\nData reset complete. Pristine state restored.")


if __name__ == "__main__":
    main()
