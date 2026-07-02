"""
08_RAG_1.py — Adaptive Structured RAG Agent (NL2SQL)

A faithful, self-contained port of the Strands Agents sample:
  strands-agents/samples → python/05-technical-use-cases/rag/
                           agentic-rag/adaptive-structured-rag

WHAT IT DOES
------------
An "adaptive structured RAG" agent that converts natural-language questions
into SQL, executes them, and self-corrects when the database returns an error.
It retrieves the database *schema* (the "retrieval" in RAG) and feeds it to the
LLM so the model can generate correct SQL grounded in real table definitions.

ADAPTATIONS FOR THIS LIMITED-PERMISSION ENVIRONMENT
---------------------------------------------------
The original sample defaults to Claude 3.7 Sonnet and supports an AWS Athena
execution mode plus a Bedrock Knowledge Base for schema retrieval. In this
environment we only have `bedrock-runtime:Converse` on `amazon.nova-lite-v1:0`
(see .kiro/steering/Permissions.md). Therefore:

  * Model      → amazon.nova-lite-v1:0  (instead of Claude 3.7 Sonnet)
  * Execution  → local SQLite only      (Athena needs athena:/s3: perms)
  * Schema RAG → hardcoded schema        (Bedrock KB needs bedrock-agent-runtime:Retrieve)

The hardcoded-schema fallback is part of the original design (get_schema's
mock path), so the agent behaves exactly as intended — just without the
optional AWS control-plane dependencies we cannot reach here.

This file is fully self-contained: it builds the SQLite database in-process
on first run, so no external setup is required.
"""

import warnings
warnings.filterwarnings(action="ignore", message=r"datetime.datetime.utcnow")

import os
import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List

from strands import Agent, tool
from strands.models import BedrockModel

logging.getLogger("strands").setLevel(logging.WARNING)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
MODEL_ID = "amazon.nova-lite-v1:0"  # Only model available with our permissions
DB_PATH = Path(__file__).parent / "data" / "wealthmanagement.db"


# --------------------------------------------------------------------------- #
# One-time database setup (mirrors the SQL in the sample's README)
# --------------------------------------------------------------------------- #
def ensure_database() -> None:
    """Create and seed the SQLite wealth-management database if it doesn't exist."""
    if DB_PATH.exists():
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE client (
                client_id INTEGER PRIMARY KEY NOT NULL,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                risk_tolerance TEXT
            );

            CREATE TABLE investment (
                investment_id INTEGER PRIMARY KEY NOT NULL,
                client_id INTEGER,
                asset_type TEXT,
                investment_amount REAL,
                current_value REAL,
                purchase_date VARCHAR,
                FOREIGN KEY (client_id) REFERENCES client(client_id)
            );

            CREATE TABLE portfolio_performance (
                client_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                total_return_percentage REAL,
                benchmark_return REAL,
                PRIMARY KEY (client_id, year),
                FOREIGN KEY (client_id) REFERENCES client(client_id)
            );

            INSERT INTO client (client_id, first_name, last_name, age, risk_tolerance) VALUES
            (1, 'John', 'Smith', 45, 'Conservative'),
            (2, 'Sarah', 'Johnson', 38, 'Moderate'),
            (3, 'Michael', 'Brown', 52, 'Aggressive'),
            (4, 'Emily', 'Davis', 29, 'Moderate'),
            (5, 'Robert', 'Wilson', 61, 'Conservative');

            INSERT INTO investment (investment_id, client_id, asset_type, investment_amount, current_value, purchase_date) VALUES
            (1, 1, 'Bonds', 50000.00, 52000.00, '2023-01-15'),
            (2, 1, 'Stocks', 30000.00, 35000.00, '2023-03-10'),
            (3, 2, 'Stocks', 75000.00, 82000.00, '2022-06-20'),
            (4, 2, 'ETF', 25000.00, 27500.00, '2023-02-05'),
            (5, 3, 'Stocks', 100000.00, 125000.00, '2022-01-10'),
            (6, 3, 'Options', 20000.00, 18000.00, '2023-05-15'),
            (7, 4, 'Mutual Funds', 40000.00, 43000.00, '2023-01-20'),
            (8, 5, 'Bonds', 80000.00, 81000.00, '2022-12-01');

            INSERT INTO portfolio_performance (client_id, year, total_return_percentage, benchmark_return) VALUES
            (1, 2022, 8.5, 7.2),
            (1, 2023, 12.3, 10.1),
            (2, 2022, 15.2, 12.8),
            (2, 2023, 18.7, 15.3),
            (3, 2022, 22.1, 18.5),
            (3, 2023, 25.8, 20.2),
            (4, 2022, 11.4, 9.8),
            (4, 2023, 14.6, 12.1),
            (5, 2022, 6.8, 5.9),
            (5, 2023, 7.2, 6.5);
            """
        )
        conn.commit()


# --------------------------------------------------------------------------- #
# Schema knowledge base (the "retrieval" part of structured RAG)
# Hardcoded fallback identical to the sample's WEALTH_MANAGEMENT_SCHEMA.
# --------------------------------------------------------------------------- #
WEALTH_MANAGEMENT_SCHEMA: List[Dict[str, Any]] = [
    {
        "table_name": "client",
        "table_description": "Contains core client information and risk profiles",
        "relationships": {"primary_key": [{"column_name": "client_id"}]},
        "columns": [
            {"Name": "client_id", "Type": "integer", "Comment": "Unique identifier for client"},
            {"Name": "first_name", "Type": "string", "Comment": "Client's first name"},
            {"Name": "last_name", "Type": "string", "Comment": "Client's last name"},
            {"Name": "age", "Type": "integer", "Comment": "Client's age"},
            {"Name": "risk_tolerance", "Type": "string", "Comment": "Client's risk tolerance level"},
        ],
    },
    {
        "table_name": "investment",
        "table_description": "Contains investment details for each client",
        "relationships": {
            "primary_key": [{"column_name": "investment_id"}],
            "foreign_keys": [{"table_name": "client", "join_on_column": "client_id"}],
        },
        "columns": [
            {"Name": "investment_id", "Type": "integer", "Comment": "Unique identifier for investment"},
            {"Name": "client_id", "Type": "integer", "Comment": "Reference to client"},
            {"Name": "asset_type", "Type": "string", "Comment": "Type of investment asset"},
            {"Name": "investment_amount", "Type": "double", "Comment": "Initial investment amount"},
            {"Name": "current_value", "Type": "double", "Comment": "Current market value of investment"},
            {"Name": "purchase_date", "Type": "date", "Comment": "Date when investment was made"},
        ],
    },
    {
        "table_name": "portfolio_performance",
        "table_description": "Contains annual portfolio performance metrics",
        "relationships": {
            "primary_key": [{"column_name": "client_id"}, {"column_name": "year"}],
            "foreign_keys": [{"table_name": "client", "join_on_column": "client_id"}],
        },
        "columns": [
            {"Name": "client_id", "Type": "integer", "Comment": "Reference to client"},
            {"Name": "year", "Type": "integer", "Comment": "Performance year"},
            {"Name": "total_return_percentage", "Type": "double", "Comment": "Annual portfolio return percentage"},
            {"Name": "benchmark_return", "Type": "double", "Comment": "Benchmark return percentage for comparison"},
        ],
    },
]


def _format_table_schema(table_info: Dict[str, Any]) -> str:
    result = f"Table: {table_info['table_name']}\n"
    result += f"Description: {table_info['table_description']}\n"
    result += "Columns:\n"
    for column in table_info["columns"]:
        result += f"- {column['Name']} ({column['Type']}): {column['Comment']}\n"
    if "relationships" in table_info:
        result += "Relationships:\n"
        if "primary_key" in table_info["relationships"]:
            pk_cols = [pk["column_name"] for pk in table_info["relationships"]["primary_key"]]
            result += f"- Primary Key: {', '.join(pk_cols)}\n"
        if "foreign_keys" in table_info["relationships"]:
            for fk in table_info["relationships"]["foreign_keys"]:
                result += f"- Foreign Key: {fk['join_on_column']} references {fk['table_name']}\n"
    return result


def _format_schema_from_data(schema_data: List[Dict[str, Any]], table_name: str = None) -> str:
    if table_name:
        table_info = next(
            (t for t in schema_data if t["table_name"].lower() == table_name.lower()), None
        )
        if not table_info:
            return f"No schema information found for table: {table_name}"
        return _format_table_schema(table_info)
    result = "Database: wealthmanagement-db\n\n"
    for table in schema_data:
        result += _format_table_schema(table) + "\n\n"
    return result


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #
@tool
def get_schema(flag: bool = False, table_name: str = None) -> str:
    """Retrieve database schema information for grounding SQL generation.

    In the full sample this queries a Bedrock Knowledge Base; here we always
    use the hardcoded wealth-management schema (the sample's fallback path),
    because Bedrock Knowledge Base retrieval is not permitted in this env.

    Args:
        flag: If True, force use of the hardcoded schema (fallback path).
        table_name: Optional specific table; if None, returns all tables.

    Returns:
        Formatted schema information for the LLM context.
    """
    return _format_schema_from_data(WEALTH_MANAGEMENT_SCHEMA, table_name)


@tool
def run_sqlite_query(query: str) -> Dict[str, Any]:
    """Execute a SQL query against the local SQLite database.

    Args:
        query: SQL query string to execute.

    Returns:
        Dict with either query results (success=True) or error info (success=False).
        Returning the error lets the agent self-correct and retry.
    """
    try:
        if not DB_PATH.exists():
            return {"success": False, "error": f"Database file not found: {DB_PATH}", "query": query}

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)

            if query.strip().upper().startswith(("SELECT", "WITH")):
                rows = cursor.fetchall()
                columns = [d[0] for d in cursor.description] if cursor.description else []
                data = [{col: row[col] for col in columns} for row in rows]
                return {"success": True, "data": data, "query": query}
            else:
                affected = cursor.rowcount
                conn.commit()
                return {
                    "success": True,
                    "data": [],
                    "affected_rows": affected,
                    "query": query,
                }

    except sqlite3.Error as e:
        return {
            "success": False,
            "error": _format_sqlite_error(str(e)),
            "sqlite_error_details": str(e),
            "query": query,
        }
    except Exception as e:  # noqa: BLE001
        return {"success": False, "error": str(e), "query": query}


def _format_sqlite_error(error_message: str) -> str:
    e = error_message.lower()
    if "no such table" in e:
        return f"Table does not exist: {error_message}"
    if "no such column" in e:
        return f"Column does not exist: {error_message}"
    if "syntax error" in e:
        return f"SQL syntax error: {error_message}"
    if "ambiguous column name" in e:
        return f"Ambiguous column name (specify table): {error_message}"
    return error_message


# --------------------------------------------------------------------------- #
# Agent factory
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """
You are an NL2SQL agent that converts natural language questions into SQL queries.

Your task is to:
1. Understand the user's question
2. Call get_schema to retrieve the database schema before writing SQL
3. Generate a valid SQL query that answers the question
4. Execute it with run_sqlite_query
5. If you receive an error, carefully analyze it, correct your SQL, and retry

When generating SQL:
- Use standard SQL syntax compatible with SQLite
- Include appropriate table joins when needed
- Use column names exactly as they appear in the schema
- When filtering on text/string values, match case-insensitively
  (e.g., use "WHERE LOWER(column) = LOWER('value')") because stored
  values may differ in capitalization from the user's wording

After you get results, present them clearly to the user in a short summary.
"""


def create_nl2sql_agent() -> Agent:
    """Create the adaptive structured RAG (NL2SQL) agent (SQLite mode)."""
    model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION, temperature=0.0)
    return Agent(
        model=model,
        tools=[get_schema, run_sqlite_query],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
def main() -> None:
    ensure_database()
    agent = create_nl2sql_agent()

    questions = [
        "How many clients do we have?",
        "Show me all conservative clients (first and last name).",
        "What's the total current value of investments for each risk tolerance level?",
        "Which client had the highest total return percentage in 2023, and what was it?",
    ]

    print("=== Adaptive Structured RAG Agent (NL2SQL, SQLite mode) ===\n")
    for q in questions:
        print(f"Q: {q}")
        response = agent(q)
        print(f"A: {response}\n")
        print("-" * 70)


if __name__ == "__main__":
    main()
