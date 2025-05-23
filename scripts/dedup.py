#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load POSTGRES_CONNECTION from root .env.local
load_dotenv(".env.local")
raw_url = os.getenv("POSTGRES_CONNECTION")
if not raw_url:
    print("Error: POSTGRES_CONNECTION not set in .env.local", file=sys.stderr)
    sys.exit(1)

# Strip asyncpg suffix if present so psycopg2 can parse
if raw_url.startswith("postgresql+asyncpg://"):
    DATABASE_URL = raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
else:
    DATABASE_URL = raw_url

def main():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1) find ISINs with duplicates
            cur.execute("""
                SELECT isin
                  FROM securities
                 WHERE isin IS NOT NULL
                 GROUP BY isin
                HAVING COUNT(*) > 1;
            """)
            dup_isins = [r["isin"] for r in cur.fetchall()]
            print(f"Found {len(dup_isins)} duplicated ISIN(s)")

            for isin in dup_isins:
                # 2) fetch all rows for this ISIN, ordered by id
                cur.execute("""
                    SELECT id, name, cusip, sedol
                      FROM securities
                     WHERE isin = %s
                     ORDER BY id;
                """, (isin,))
                rows = cur.fetchall()
                keeper = rows[0]
                duplicates = rows[1:]
                keeper_id = keeper["id"]
                dup_ids   = [r["id"] for r in duplicates]

                # 3) merge fields
                merged_cusip = next((r["cusip"] for r in rows if r["cusip"]), None)
                merged_sedol = next((r["sedol"] for r in rows if r["sedol"]), None)
                merged_name  = max((r["name"] or "" for r in rows), key=len)

                # update keeper if values changed
                if (keeper["cusip"], keeper["sedol"], keeper["name"]) != (merged_cusip, merged_sedol, merged_name):
                    cur.execute("""
                        UPDATE securities
                           SET cusip = %s,
                               sedol = %s,
                               name  = %s
                         WHERE id = %s;
                    """, (merged_cusip, merged_sedol, merged_name, keeper_id))
                    print(f"  Updated security id={keeper_id}")

                # 4) delete the duplicate rows
                if dup_ids:
                    cur.execute("DELETE FROM securities WHERE id = ANY(%s);", (dup_ids,))
                    print(f"  Deleted duplicate securities {dup_ids}")

        conn.commit()
        print("Deduplication complete.")

if __name__ == "__main__":
    main()
