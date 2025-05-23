#!/usr/bin/env python3
import asyncio
import csv
from pathlib import Path
import aiofiles
from martini.fitch import FitchScraper

INPUT_CSV = Path("data/isin_list.csv")
NO_RESULT_PLACEHOLDER = "<NO_RESULT>"

async def fetch_name(isin: str) -> str | None:
    """
    Fetch security name for a given ISIN using FitchScraper.
    Returns:
      - str: security name if found
      - "" (empty str): if no results (expected ValueError)
      - None: if unexpected error occurred
    """
    scraper = FitchScraper(isin)
    try:
        name = await scraper.fetch_security_name()
        return name or ""
    except ValueError as e:
        # expected case: no results
        print(f"No results for {isin}, leaving blank: {e}")
        return ""
    except Exception as e:
        # unexpected error: skip updating
        print(f"Error fetching name for {isin}, will retry later: {e}")
        return None

async def write_csv(rows, fieldnames):
    """Asynchronously overwrite the CSV with current rows."""
    async with aiofiles.open(INPUT_CSV, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        await outfile.write(','.join(fieldnames) + '\n')
        for row in rows:
            line = ','.join([row.get(fn, '') for fn in fieldnames]) + '\n'
            await outfile.write(line)

async def main():
    # Load CSV
    async with aiofiles.open(INPUT_CSV, mode='r', encoding='utf-8', newline='') as infile:
        content = await infile.read()
    lines = content.splitlines()
    reader = csv.DictReader(lines)
    fieldnames = reader.fieldnames
    rows = list(reader)

    # Process rows, skip if name or marked NO_RESULT
    for idx, row in enumerate(rows):
        isin = row.get('isin', '').strip()
        name = row.get('name', '').strip()
        if not isin or name not in ('', None):
            continue

        print(f"Fetching name for {isin}...")
        fetched = await fetch_name(isin)
        # If unexpected error, skip update
        if fetched is None:
            continue

        if fetched == "":
            # No results case
            print(f"  No name found for {isin}, marking {NO_RESULT_PLACEHOLDER}")
            rows[idx]['name'] = NO_RESULT_PLACEHOLDER
        else:
            # Found a valid name
            print(f"  Found: {fetched}")
            rows[idx]['name'] = fetched

        # Persist update immediately
        await write_csv(rows, fieldnames)

if __name__ == '__main__':
    asyncio.run(main())
