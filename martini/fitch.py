import argparse
import asyncio
import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError
from .utils.http_helper import get_random_user_agent

class FitchScraper:
    BASE_URL = (
        "https://www.fitchratings.com/search/"
        "?expanded=issue&isIdentifier=true&query={isin}"
    )

    # Default cookie string for Fitch
    COOKIE_STRING = (
        "SSSC_P=1.G7507522358643580571.1|139.5066:146.5445:149.5552:173.6256:178.6425; "
        "SSOD_P=ADk9AAAAEgC6AAAAAQAAAM8TMGjPEzBoAQAAAA; "
        "_gcl_au=1.1.895592303.1747981264; "
        "_mkto_trk=id:732-CKH-767&token:_mch-fitchratings.com-4fef24dba5f251a42d9a422886c5356; "
        "isFitchInternal=false; "
        "kndctr_EED229A963BD58F20A495FAB_AdobeOrg_cluster=jpn3; "
        "kndctr_EED229A963BD58F20A495FAB_AdobeOrg_identity=CiYzMzU1MTgwNzExOTg0NzEyNTA1NDExMjAzMzg1MjUyMTA5MDczM1ITCLLTtd7vMhABGAEqBEpQTjMwAPABstO13u8y; "
        "SSRT_P=0RMwaAADAA; "
        "SSID_P=CQCOvh1GAAAAAADPEzBom95AAs8TMGgBAAAAAAAAAAAAzxMwaAC337IAAAMZGQAAzxMwaAEAkgAAA0UVAADPEzBoAQCLAAAByhMAAM8TMGgBAJUAAAGwFQAAzxMwaAEArQAAAXAYAADPEzBoAQA"
    )

    def __init__(self, isin: str, debug_dir: str = "debug"):
        self.isin = isin
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)

    async def fetch_security_name(self) -> str:
        """
        Launches a headless browser, adds headers and cookies, navigates to the search URL,
        then waits up to 10 seconds for either a "No Results!" title or the result link to appear.
        Raises if no results, returns the security name otherwise. Saves debug info on failure.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        debug_prefix = self.debug_dir / f"{self.isin}_{timestamp}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=get_random_user_agent())
            # set cookies
            await context.add_cookies([
                {
                    'name': part.strip().split('=')[0],
                    'value': part.strip().split('=')[1],
                    'domain': 'www.fitchratings.com',
                    'path': '/',
                    'httpOnly': False,
                    'secure': True,
                }
                for part in self.COOKIE_STRING.split(';') if part.strip() and '=' in part
            ])
            page = await context.new_page()
            await page.set_extra_http_headers({
                'cookie': self.COOKIE_STRING,
                'user-agent': get_random_user_agent()
            })

            try:
                await page.goto(self.BASE_URL.format(isin=self.isin), timeout=60000)

                # Race between "No Results!" and result link (10s)
                no_results_task = asyncio.create_task(
                    page.wait_for_selector('div.column__left.search__no-results--title', timeout=10000)
                )
                link_task = asyncio.create_task(
                    page.wait_for_selector('h3.heading--5 a', timeout=10000)
                )

                done, pending = await asyncio.wait(
                    {no_results_task, link_task},
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=10
                )
                # Cancel whichever didn't complete
                for task in pending:
                    task.cancel()

                if no_results_task in done:
                    # Found no-results first
                    raise ValueError(f"No results found for ISIN: {self.isin}")

                # Otherwise, result link appeared
                link_element = done.pop().result()
                if not link_element:
                    raise ValueError("Result link not found")

                name = await link_element.get_attribute("aria-label")
                return name

            except Exception as e:
                # Save debugging info
                await page.screenshot(path=str(debug_prefix) + ".png", full_page=True)
                html = await page.content()
                (debug_prefix.with_suffix('.html')).write_text(html, encoding='utf-8')
                raise

            finally:
                await browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Fitch Ratings for a security name by ISIN."
    )
    parser.add_argument(
        "isin",
        type=str,
        help="The ISIN code of the security to search for",
    )
    parser.add_argument(
        "--debug-dir",
        type=str,
        default="debug",
        help="Directory to save debug screenshots and HTML",
    )
    args = parser.parse_args()

    scraper = FitchScraper(args.isin, args.debug_dir)
    try:
        name = asyncio.run(scraper.fetch_security_name())
        print(name)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
