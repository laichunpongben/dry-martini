#!/usr/bin/env python3
import os
import glob
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")
DB_URL = os.getenv("POSTGRES_CONNECTION")
if not DB_URL:
    raise RuntimeError("Please set POSTGRES_CONNECTION in your environment")

# Parse connection URL
res = urlparse(DB_URL)
conn_info = {
    "dbname": res.path.lstrip("/"),
    "user": res.username,
    "password": res.password,
    "host": res.hostname,
    "port": res.port or 5432,
}

def ensure_holdings_table(conn):
    """
    Create fund_holdings table if it doesn't exist.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS fund_holdings (
              id SERIAL PRIMARY KEY,
              fund_id INTEGER NOT NULL REFERENCES funds(id),
              security_id INTEGER NOT NULL REFERENCES securities(id),
              pct_of_portfolio NUMERIC(7,4),
              UNIQUE(fund_id, security_id)
            );
            """
        )
    conn.commit()


def upsert_security(cur, sec_name, cusip, isin, sedol):
    """
    Insert security if not exists, or return existing. Handles null isin via other identifiers.
    """
    cur.execute(
        "SELECT id FROM securities WHERE "
        "(isin IS NOT NULL AND isin = %s) OR "
        "(cusip IS NOT NULL AND cusip = %s) OR "
        "(sedol IS NOT NULL AND sedol = %s)",
        (isin, cusip, sedol)
    )
    row = cur.fetchone()
    if row:
        return row[0]
    # Use correct column name 'name' instead of 'security_name'
    cur.execute(
        "INSERT INTO securities (name, cusip, isin, sedol) "
        "VALUES (%s, %s, %s, %s) RETURNING id;",
        (sec_name, cusip, isin, sedol)
    )
    return cur.fetchone()[0]


def load_csv(conn, path):
    """
    Load a CSV of holdings, upsert securities if needed, and upsert into fund_holdings.
    Assumes funds table already exists and has matching entries.
    """
    df = pd.read_csv(path)
    fund_name = os.path.splitext(os.path.basename(path))[0].replace("_", " ").title()
    report_date = "2025-04-30"  # adjust or parse as needed

    with conn.cursor() as cur:
        # Get existing fund_id
        cur.execute(
            "SELECT id FROM funds WHERE fund_name = %s AND report_date = %s",
            (fund_name, report_date)
        )
        result = cur.fetchone()
        if not result:
            raise ValueError(f"Fund not found: {fund_name} on {report_date}")
        fund_id = result[0]

        rows = []
        for _, row in df.iterrows():
            # Clean identifiers, converting NaN to None
            sec_name = row.get("SECURITY NAME")
            isin = row.get("ISIN")
            cusip = row.get("CUSIP")
            sedol = row.get("SEDOL")
            if pd.isna(isin): isin = None
            if pd.isna(cusip): cusip = None
            if pd.isna(sedol): sedol = None

            # Upsert security if not found or ISIN is null
            sec_id = upsert_security(cur, sec_name, cusip, isin, sedol)
            rows.append((fund_id, sec_id, row["% OF PORTFOLIO"]))

        # Bulk upsert holdings
        execute_values(
            cur,
            """
            INSERT INTO fund_holdings (fund_id, security_id, pct_of_portfolio)
            VALUES %s
            ON CONFLICT (fund_id, security_id)
            DO UPDATE SET pct_of_portfolio = EXCLUDED.pct_of_portfolio;
            """,
            rows
        )
    conn.commit()
    print(f"Loaded {len(df)} rows from {path}")


def main():
    conn = psycopg2.connect(**conn_info)
    ensure_holdings_table(conn)
    for csv_file in glob.glob("data/funds/*.csv"):
        load_csv(conn, csv_file)
    conn.close()


if __name__ == "__main__":
    main()
