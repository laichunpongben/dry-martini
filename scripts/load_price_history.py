# load_price_history.py

import os
import asyncio
import argparse
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

from martini.frankfurt import FrankfurtScraper

# 1) Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")


def insert_price_history(df: pd.DataFrame, dsn: str, isin: str):
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    # lookup security_id
    cur.execute("SELECT id FROM securities WHERE isin = %s", (isin,))
    row = cur.fetchone()
    if not row:
        print(f"⚠️ ISIN {isin} not found in securities table, skipping.")
        cur.close()
        conn.close()
        return
    security_id = row[0]

    records = []
    for _, r in df.iterrows():
        date       = pd.to_datetime(r['date'], dayfirst=True).date()
        open_v     = float(r['open'].strip('%'))
        close_v    = float(r['close'].strip('%'))
        high_v     = float(r['high'].strip('%'))
        low_v      = float(r['low'].strip('%'))

        raw_vol     = r.get('volume')
        vol         = int(raw_vol.replace(',', '')) if raw_vol not in (None, '', 'nan') else None

        raw_vol_nom = r.get('volume_nominal')
        vol_nom     = int(raw_vol_nom.replace(',', '')) if raw_vol_nom not in (None, '', 'nan') else None

        records.append((
            security_id,
            date,
            open_v,
            close_v,
            high_v,
            low_v,
            vol,
            vol_nom
        ))

    sql = """
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
    """
    execute_values(cur, sql, records)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted/Updated {len(records)} rows for ISIN {isin}")


def fetch_all_isins(dsn: str):
    """
    Fetches all non-null ISIN codes from securities table.
    """
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("SELECT isin FROM securities WHERE isin IS NOT NULL;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]


def main():
    parser = argparse.ArgumentParser(
        description="Fetch price history via FrankfurtScraper and insert into Postgres"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--isin", help="Single ISIN code to process, e.g. DE000A383J95")
    group.add_argument("--all", action="store_true", help="Process all ISINs from securities table")
    parser.add_argument(
        "--save-csv",
        action="store_true",
        default=False,
        help="Save intermediate CSV files (default: no)"
    )

    args = parser.parse_args()

    dsn = os.getenv("POSTGRES_CONNECTION")
    if not dsn:
        parser.error("Environment variable POSTGRES_CONNECTION not set (from .env.local)")

    if args.all:
        isins = fetch_all_isins(dsn)
    else:
        isins = [args.isin]

    scraper = FrankfurtScraper()

    for isin in isins:
        print(f"\n🔄 Processing ISIN: {isin}")
        try:
            df = asyncio.run(scraper.fetch_price_history(isin))
        except Exception as e:
            print(f"❌ Error fetching data for {isin}: {e}")
            continue

        if df.empty:
            print(f"❌ No price history for ISIN {isin}, skipping.")
            continue

        df.columns = (
            df.columns
              .str.strip()
              .str.lower()
              .str.replace(' ', '_', regex=False)
        )

        if args.save_csv:
            csv_path = f"price_history_{isin}.csv"
            df.to_csv(csv_path, index=False)
            print(f"💾 Saved intermediate CSV to {csv_path}")

        insert_price_history(df, dsn, isin)


if __name__ == "__main__":
    main()
