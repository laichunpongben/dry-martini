# frankfurt.py

import asyncio
import argparse
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from .utils.http_helper import get_random_user_agent  # Use helper for User-Agent

# Constants for timeouts and typing behavior
DEFAULT_TIMEOUT = 5000   # ms, 5 seconds for most actions
GOTO_TIMEOUT = 60000     # ms, 60 seconds for navigation
TYPE_DELAY = 150         # ms delay between keystrokes to mimic human typing

class FrankfurtScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def fetch_price_history(self, isin: str) -> pd.DataFrame:
        """
        Fetch the price history table for a given ISIN and return as a pandas DataFrame.
        """
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context()

            # Set timeouts and custom User-Agent header
            context.set_default_timeout(DEFAULT_TIMEOUT)
            headers = {"User-Agent": get_random_user_agent()}
            await context.set_extra_http_headers(headers)

            page = await context.new_page()
            try:
                # Navigate to site and accept cookies
                await page.goto("https://www.boerse-frankfurt.de/en", timeout=GOTO_TIMEOUT)
                accept_btn = page.locator("button#cookie-hint-btn-accept")
                if await accept_btn.count() > 0:
                    await accept_btn.click()

                # Search for ISIN
                await page.wait_for_selector("input#mat-input-0")
                await page.focus("input#mat-input-0")
                await page.evaluate(
                    "selector => document.querySelector(selector).value = ''",
                    "input#mat-input-0"
                )
                await page.keyboard.type(isin, delay=TYPE_DELAY)

                # Wait for suggestion elements; if none appear, treat as missing
                try:
                    await page.wait_for_selector(
                        "div.global-search-result-option", timeout=DEFAULT_TIMEOUT
                    )
                except PlaywrightTimeoutError:
                    print(f"⚠️ ISIN '{isin}' not found on Börse Frankfurt. No data returned.")
                    return pd.DataFrame()

                # Choose the matching suggestion
                suggestion = page.locator(
                    f"div.global-search-result-option:has(.isin:has-text('{isin}'))"
                )
                if await suggestion.count() == 0:
                    print(f"⚠️ ISIN '{isin}' not found in suggestions. No data returned.")
                    return pd.DataFrame()

                await suggestion.click(force=True)
                await page.wait_for_timeout(DEFAULT_TIMEOUT)

                # Click 'Price History'
                price_btn = page.locator(
                    "button.data-menue-button.btn.btn-lg-customized:has-text('Price History')"
                )
                await price_btn.click()
                await page.wait_for_selector(
                    "table.widget-table", timeout=DEFAULT_TIMEOUT
                )

                # Collect table data across pages
                records = []
                header_cells = await page.locator(
                    "table.widget-table thead tr th"
                ).all_text_contents()

                while True:
                    rows = page.locator("table.widget-table tbody tr")
                    count = await rows.count()
                    for i in range(count):
                        cells = await rows.nth(i).locator("td").all_text_contents()
                        records.append(cells)
                    next_btn = page.locator(
                        "button.page-bar-type-button.btn.btn-lg:has(span.icon-arrow-step-right-grey-big)"
                    ).first
                    if not await next_btn.is_enabled():
                        break
                    await next_btn.click()
                    await page.wait_for_timeout(1000)

                df = pd.DataFrame(records, columns=header_cells)
                return df

            except PlaywrightTimeoutError as e:
                debug_path = "debug.png"
                await page.screenshot(path=debug_path, full_page=True)
                print(f"⚠️ Debug screenshot saved to {debug_path}")
                print(f"⏱ Action timed out: {e}")
                raise

            finally:
                await browser.close()

    def save_price_history(self, df: pd.DataFrame, csv_path: str):
        """
        Save the price history DataFrame to a CSV file.
        """
        df.to_csv(csv_path, index=False)
        print(f"✅ Price history saved to {csv_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch price history for a given ISIN and save as CSV."
    )
    parser.add_argument(
        "isin",
        help="ISIN code to search for (e.g. DE000A383J95)"
    )
    parser.add_argument(
        "-o", "--output",
        default="price_history.csv",
        help="Path to output CSV file"
    )
    args = parser.parse_args()

    scraper = FrankfurtScraper()
    df = asyncio.run(scraper.fetch_price_history(args.isin))
    scraper.save_price_history(df, args.output)


if __name__ == "__main__":
    main()
