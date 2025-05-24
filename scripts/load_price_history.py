# load_price_history.py

import os
import asyncio
import argparse
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

from martini.frankfurt import FrankfurtScraper

# 1) Load environment variables from .env.local (won't override existing OS env vars)
load_dotenv(dotenv_path=".env.local")  # :contentReference[oaicite:0]{index=0}

def insert_price_history(df: pd.DataFrame, dsn: str, isin: str):
    """
    Insert DataFrame rows into Postgres price_history table.
    Expects DSN like 'postgresql://user:pass@host:port/dbname'.
    """
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    # lookup security_id
    cur.execute("SELECT id FROM securities WHERE isin = %s", (isin,))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"ISIN {isin} not found in securities table")
    security_id = row[0]

    # prepare data: parse date and strip percent signs
    records = []
    for _, r in df.iterrows():
        date     = pd.to_datetime(r['Date'], dayfirst=True).date()
        open_v   = float(r['Open'].strip('%'))
        close_v  = float(r['Close'].strip('%'))
        high_v   = float(r['High'].strip('%'))
        low_v    = float(r['Low'].strip('%'))
        vol      = int(r['Volume']) if r.get('Volume') not in (None, '', 'nan') else None
        vol_nom  = int(r['Volume nominal']) if r.get('Volume nominal') not in (None, '', 'nan') else None
        records.append((security_id, date, open_v, close_v, high_v, low_v, vol, vol_nom))

    sql = '''
        INSERT INTO price_history
          (security_id, date, open, close, high, low, volume, volume_nominal)
        VALUES %s
        ON CONFLICT (security_id, date) DO UPDATE
          SET open = EXCLUDED.open,
              close = EXCLUDED.close,
              high = EXCLUDED.high,
              low = EXCLUDED.low,
              volume = EXCLUDED.volume,
              volume_nominal = EXCLUDED.volume_nominal;
    '''
    execute_values(cur, sql, records)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted/Updated {len(records)} rows for ISIN {isin}")

def main():
    parser = argparse.ArgumentParser(
        description="Fetch price history via FrankfurtScraper and insert into Postgres"
    )
    parser.add_argument("isin", help="ISIN code to process, e.g. DE000A383J95")
    args = parser.parse_args()

    # 2) Read DSN from environment
    dsn = os.getenv("POSTGRES_CONNECTION")
    if not dsn:
        parser.error("Environment variable POSTGRES_CONNECTION not set (from .env.local)")

    scraper = FrankfurtScraper()
    df = asyncio.run(scraper.fetch_price_history(args.isin))

    # 3) Optionally save to CSV
    csv_path = f"price_history_{args.isin}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved intermediate CSV to {csv_path}")

    # 4) Insert into Postgres
    insert_price_history(df, dsn, args.isin)

if __name__ == "__main__":
    main()
