#!/usr/bin/env python3
import os
import glob
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load .env with SUPABASE_URL and SUPABASE_ANON_KEY or directly set:
#   POSTGRES_CONNECTION=postgresql://<user>:<pass>@<host>:<port>/<db>
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

def ensure_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS funds (
          id           SERIAL PRIMARY KEY,
          fund_name    TEXT NOT NULL,
          report_date  DATE NOT NULL,
          UNIQUE(fund_name, report_date)
        );
        CREATE TABLE IF NOT EXISTS securities (
          id                SERIAL PRIMARY KEY,
          security_name     TEXT NOT NULL,
          cusip             VARCHAR(12),
          isin              VARCHAR(15),
          sedol             VARCHAR(12),
          UNIQUE(cusip, isin, sedol)
        );
        CREATE TABLE IF NOT EXISTS fund_holdings (
          id                SERIAL PRIMARY KEY,
          fund_id           INTEGER NOT NULL REFERENCES funds(id),
          security_id       INTEGER NOT NULL REFERENCES securities(id),
          pct_of_portfolio  NUMERIC(7,4),
          UNIQUE(fund_id, security_id)
        );
        """)
    conn.commit()

def upsert_fund(cur, name, report_date):
    cur.execute("""
      INSERT INTO funds (fund_name, report_date)
      VALUES (%s, %s)
      ON CONFLICT (fund_name, report_date) DO UPDATE
        SET fund_name = EXCLUDED.fund_name
      RETURNING id;
    """, (name, report_date))
    return cur.fetchone()[0]

def upsert_security(cur, sec_name, cusip, isin, sedol):
    cur.execute("""
      INSERT INTO securities (security_name, cusip, isin, sedol)
      VALUES (%s, %s, %s, %s)
      ON CONFLICT (cusip, isin, sedol) DO UPDATE
        SET security_name = EXCLUDED.security_name
      RETURNING id;
    """, (sec_name, cusip, isin, sedol))
    return cur.fetchone()[0]

def load_csv(conn, path):
    df = pd.read_csv(path)
    # Expect columns: SECURITY NAME,CUSIP,ISIN,SEDOL,% OF PORTFOLIO
    fund_name = os.path.splitext(os.path.basename(path))[0].replace("_", " ").title()
    # Infer date from CSV name or hardcode if needed
    # e.g. euro_corporate_bond_fund -> 2025-04-30
    report_date = "2025-04-30"

    with conn.cursor() as cur:
        fund_id = upsert_fund(cur, fund_name, report_date)

        # Prepare securities upsert and holding inserts
        rows = []
        for _, row in df.iterrows():
            sec_id = upsert_security(
                cur,
                row["SECURITY NAME"],
                row.get("CUSIP"),
                row.get("ISIN"),
                row.get("SEDOL"),
            )
            rows.append((fund_id, sec_id, row["% OF PORTFOLIO"]))

        # Bulk upsert holdings
        execute_values(cur, """
          INSERT INTO fund_holdings(fund_id, security_id, pct_of_portfolio)
          VALUES %s
          ON CONFLICT (fund_id, security_id) DO UPDATE
            SET pct_of_portfolio = EXCLUDED.pct_of_portfolio;
        """, rows)

    conn.commit()
    print(f"Loaded {len(df)} rows from {path}")

def main():
    conn = psycopg2.connect(**conn_info)
    ensure_tables(conn)

    for csv_file in glob.glob("data/funds/*.csv"):
        load_csv(conn, csv_file)

    conn.close()

if __name__ == "__main__":
    main()
