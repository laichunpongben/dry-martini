# emma.py

import asyncio
import sys
import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.async_api import (
    async_playwright,
    Page,
    BrowserContext,
    TimeoutError as PlaywrightTimeout,
)

# --- Configuration constants (cookies, headers, consent selector) ---
INITIAL_COOKIES = {
    "ASP.NET_SessionId": "5rvoz4yi3oe2dm4zae4pb1v5",
    "__utma": "247245968.538474743.1747667123.1747667123.1747667123.1",
    "__utmc": "247245968",
    "__utmz": "247245968.1747667123.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
    "__utmt": "1",
    "_ga": "GA1.1.773426685.1747667124",
    "MostRecentRequestTimeInTicks": "638832495350219966",
    "Disclaimer6": "msrborg",
    "elf-initial": "elf-initial-markup",
    "acceptCookies": "true",
    "__utmb": "247245968.7.10.1747667123",
    "_ga_X7VJ8QGMQ9": "GS2.1.s1747667123$o1$g1$t1747667123$j0$l0$h0"
}

EXTRA_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "upgrade-insecure-requests": "1",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
}

CONSENT_SELECTOR = "#ctl00_mainContentArea_disclaimerContent_yesButton"


class EMMABaseScraper(ABC):
    """
    Base scraper for EMMA (MSRB) municipal bond pages.
    Handles browser setup, consent overlay, and teardown.
    """

    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.out_dir.mkdir(exist_ok=True, parents=True)

    @abstractmethod
    def build_url(self, **kwargs) -> str:
        """Return the full URL for this EMMA scrape task."""
        ...

    @abstractmethod
    async def parse_and_save(self, page: Page, **kwargs) -> None:
        """Do the page interactions and save extracted data into out_dir."""
        ...

    async def handle_consent(self, page: Page, context: BrowserContext):
        """Click the EMMA Terms-of-Use overlay if it appears, updating headers."""
        try:
            btn = page.locator(CONSENT_SELECTOR)
            if await btn.count() > 0:
                print("[DEBUG] Accepting EMMA ToU...", file=sys.stderr)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(500)
                await btn.click(timeout=10000)
                await page.wait_for_selector(CONSENT_SELECTOR, state="detached", timeout=10000)
                cookies = await context.cookies()
                cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                await context.set_extra_http_headers({**EXTRA_HEADERS, "cookie": cookie_header})
                print("[DEBUG] EMMA ToU accepted; headers updated.", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] EMMA consent handling failed: {e}", file=sys.stderr)

    async def run(self, **kwargs):
        """Launch browser, navigate to URL, handle consent, parse & save, then close."""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context()
            # seed cookies and headers
            await context.add_cookies([
                {**{"domain": "emma.msrb.org", "path": "/"}, **{"name": k, "value": v}}
                for k, v in INITIAL_COOKIES.items()
            ])
            await context.set_extra_http_headers(EXTRA_HEADERS)
            page = await context.new_page()

            url = self.build_url(**kwargs)
            try:
                print(f"[DEBUG] Navigating to {url}", file=sys.stderr)
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await self.handle_consent(page, context)
                # perform parsing; capture return value for aggregations
                result = await self.parse_and_save(page, context=context, **kwargs)
                return result
            except PlaywrightTimeout as te:
                print(f"[ERROR] Timeout at {url}: {te}", file=sys.stderr)
                await page.screenshot(path=str(self.out_dir / "timeout.png"))
                (self.out_dir / "timeout.html").write_text(await page.content(), encoding="utf-8")
            except Exception as e:
                print(f"[ERROR] EMMA scrape failed: {e}", file=sys.stderr)
                await page.screenshot(path=str(self.out_dir / "error.png"))
                (self.out_dir / "error.html").write_text(await page.content(), encoding="utf-8")
            finally:
                await browser.close()
                print("[DEBUG] Browser closed.", file=sys.stderr)


class EMMASecurityDetailScraper(EMMABaseScraper):
    def build_url(self, cusip: str, **_) -> str:
        return f"https://emma.msrb.org/Security/Details/?id={cusip}"

    async def parse_and_save(self, page: Page, **kwargs) -> None:
        cusip = kwargs["cusip"]
        # --- HANDLE MISSING CUSIP ---
        if await page.locator("div.error-content").count() > 0:
            msg = await page.locator("div.error-content span").inner_text()
            print(f"[ERROR] No records for CUSIP {cusip}: {msg}", file=sys.stderr)
            return

        # --- TRADE SUMMARY ---
        summary_sel = "ul.nav.TA-nav li a:has-text('Trade Summary')"
        await page.wait_for_selector(summary_sel, timeout=15000)
        await page.click(summary_sel)
        await page.wait_for_selector("#lvRollup_wrapper", timeout=15000)

        rows = await page.locator("table#lvRollup tbody tr").all()
        trades = [
            [(await td.inner_text()).strip() for td in await row.locator("td").all()]
            for row in rows
        ]
        trades_file = self.out_dir / "trades.csv"
        with open(trades_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Trade Date", "High/Low Price", "High/Low Yield",
                "Trade Count", "Total Trade Amount"
            ])
            writer.writerows(trades)
        print(f"✅ Saved {len(trades)} trades to {trades_file.name}", file=sys.stderr)

        # --- RATINGS ---
        await page.click("a#ui-id-3")
        await self.handle_consent(page, context=page.context)
        await page.wait_for_selector("#ratings", timeout=15000)
        ratings_text = await page.locator("#ratings").inner_text()
        ratings_file = self.out_dir / "ratings.txt"
        with open(ratings_file, "w") as f:
            f.write(ratings_text)
        print(f"✅ Saved ratings to {ratings_file.name}", file=sys.stderr)

        # --- DISCLOSURES ---
        await page.click("a#ui-id-4")
        await self.handle_consent(page, context=page.context)
        await page.wait_for_selector("#officialStatementContainer table", timeout=15000)
        dr = await page.locator("#officialStatementContainer tbody tr").all()
        disclosures = [
            [(await tr.locator("a").inner_text()).strip(),
             (await tr.locator("td:last-child").inner_text()).strip()]
            for tr in dr
        ]
        disclosures_file = self.out_dir / "disclosures.csv"
        with open(disclosures_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Document", "Posted Date"])
            writer.writerows(disclosures)
        print(f"✅ Saved disclosures to {disclosures_file.name}", file=sys.stderr)

        # --- FINAL SCALE ---
        await page.click("a#ui-id-5")
        await self.handle_consent(page, context=page.context)
        await page.wait_for_selector("table#dtSecurities tbody tr", timeout=15000)
        fs_rows = await page.locator("table#dtSecurities tbody tr").all()
        final = []
        for tr in fs_rows:
            tds = await tr.locator("td").all()
            c9 = await tds[0].locator("img").get_attribute("data-cusip9")
            pri = (await tds[1].inner_text()).strip()
            cop = (await tds[3].inner_text()).strip()
            mat = (await tds[4].inner_text()).strip()
            rts = []
            for td in tds[7:]:
                if await td.locator("img").count():
                    rts.append(await td.locator("img").get_attribute("data-rating"))
            final.append([c9, pri, cop, mat, ",".join(rts)])
        final_file = self.out_dir / "final_scale.csv"
        with open(final_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["CUSIP", "Principal", "Coupon", "Maturity", "Ratings"])
            writer.writerows(final)
        print(f"✅ Saved final scale to {final_file.name}", file=sys.stderr)


class EMMAStateIssuersScraper(EMMABaseScraper):
    def build_url(self, state: str, **_) -> str:
        return f"https://emma.msrb.org/IssuerHomePage/State?state={state}"

    async def parse_and_save(self, page: Page, **kwargs):
        state = kwargs.get("state")
        # support aggregation mode: skip file write and return data
        aggregate = kwargs.get("aggregate", False)
        # Set to 100 per page
        await page.wait_for_selector("select[name='lvIssuers_length']", timeout=15000)
        await page.select_option("select[name='lvIssuers_length']", value="100")
        await page.wait_for_timeout(1000)

        all_data = []
        while True:
            await page.wait_for_selector("table#lvIssuers tbody tr", timeout=15000)
            rows = await page.locator("table#lvIssuers tbody tr").all()
            for r in rows:
                link = r.locator("td a")
                name = (await link.inner_text()).strip()
                href = await link.get_attribute("href")
                qs = parse_qs(urlparse(href).query)
                all_data.append([name, qs.get("id", [""])[0], qs.get("type", [""])[0]])

            next_btn = page.locator("a#lvIssuers_next")
            if "disabled" in (await next_btn.get_attribute("class") or ""):
                break
            await next_btn.click()
            await page.wait_for_timeout(1000)

        # if aggregating, return collected rows without writing file
        if aggregate:
            return all_data
        issuers_file = self.out_dir / "issuers.csv"
        with open(issuers_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Issuer Name", "Issuer ID", "Issuer Type"])
            writer.writerows(all_data)
        print(f"✅ Saved {len(all_data)} issuers to {issuers_file.name}", file=sys.stderr)


class EMMAIssuerDetailScraper(EMMABaseScraper):
    def build_url(self, id: str, **_) -> str:
        return f"https://emma.msrb.org/IssuerHomePage/Issuer?id={id}"

    async def parse_and_save(self, page: Page, context: BrowserContext, **kwargs) -> None:
        id_ = kwargs["id"]

        # --- ISSUES TAB ---
        await page.wait_for_selector("li[data-cid='t-iss']", timeout=15000)
        await page.click("li[data-cid='t-iss']")
        await page.wait_for_selector("select[name='lvIssues_length']", timeout=15000)
        await page.select_option("select[name='lvIssues_length']", value="100")
        await page.wait_for_timeout(1000)
        issues = []
        while True:
            await page.wait_for_selector("table#lvIssues tbody tr", timeout=15000)
            rows = await page.locator("table#lvIssues tbody tr").all()
            for r in rows:
                link = r.locator("td:nth-child(1) a")
                href = await link.get_attribute("href")
                issue_id = href.rsplit("/", 1)[-1]
                desc = (await link.inner_text()).strip()
                dated = (await r.locator("td:nth-child(2)").inner_text()).strip()
                mat = (await r.locator("td:nth-child(3)").inner_text()).strip()
                issues.append([issue_id, desc, dated, mat])
            nxt = page.locator("a#lvIssues_next")
            if "disabled" in (await nxt.get_attribute("class") or ""):
                break
            await nxt.click()
            await page.wait_for_timeout(1000)
        issues_file = self.out_dir / "issues.csv"
        with open(issues_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Issue ID", "Issue Description", "Dated Date", "Maturity Dates"])
            writer.writerows(issues)
        print(f"✅ Saved {len(issues)} issues to {issues_file.name}", file=sys.stderr)

        # --- OFFICIAL STATEMENTS TAB ---
        await page.click("li[data-cid='t-os']")
        # prepare directory for official statements PDFs
        official_dir = self.out_dir / "official_statements"
        official_dir.mkdir(exist_ok=True, parents=True)
        await page.wait_for_selector("select[name='lvOS_length']", timeout=15000)
        await page.select_option("select[name='lvOS_length']", value="100")
        await page.wait_for_timeout(1000)
        all_pdfs = []
        while True:
            await page.wait_for_selector("table#lvOS tbody tr", timeout=15000)
            rows = await page.locator("table#lvOS tbody tr").all()
            for r in rows:
                a = r.locator("td.fidW a")
                href = await a.get_attribute("href")
                pdf_url = urljoin("https://emma.msrb.org", href)
                filename = Path(urlparse(href).path).name
                out_path = official_dir / filename
                if out_path.exists():
                    print(f"[DEBUG] Skipping existing {filename}", file=sys.stderr)
                else:
                    print(f"[DEBUG] Downloading {pdf_url} → {filename}", file=sys.stderr)
                    resp = await context.request.get(pdf_url)
                    out_path.write_bytes(await resp.body())
                all_pdfs.append(filename)
            nxt = page.locator("a#lvOS_next")
            if "disabled" in (await nxt.get_attribute("class") or ""):
                break
            await nxt.click()
            await page.wait_for_timeout(1000)
        print(f"✅ Downloaded or skipped {len(all_pdfs)} official statements for issuer id={id_}", file=sys.stderr)

        # --- FINANCIAL DISCLOSURES TAB ---
        await page.click("li[data-cid='t-fcd']")
        # prepare directory for financial disclosures PDFs
        fcd_dir = self.out_dir / "financial_disclosures"
        fcd_dir.mkdir(exist_ok=True, parents=True)
        # Wait for either the disclosures dropdown or a visible no-record message
        await page.wait_for_selector(
            "select[name='lvFCD_length'], div#t-fcd p.no-record:visible",
            timeout=15000
        )
        # If the no-record message is visible, skip downloading
        if await page.is_visible("div#t-fcd p.no-record"):
            print(f"[WARN] No financial disclosures for issuer id={id_}", file=sys.stderr)
            return
        await page.select_option("select[name='lvFCD_length']", value="100")
        await page.wait_for_timeout(1000)
        all_fcd = []
        while True:
            await page.wait_for_selector("table#lvFCD tbody tr", timeout=15000)
            rows = await page.locator("table#lvFCD tbody tr").all()
            for r in rows:
                a = r.locator("td.fidW a")
                href = await a.get_attribute("href")
                pdf_url = urljoin("https://emma.msrb.org", href)
                filename = Path(urlparse(href).path).name
                out_path = fcd_dir / filename
                if out_path.exists():
                    print(f"[DEBUG] Skipping existing {filename}", file=sys.stderr)
                else:
                    print(f"[DEBUG] Downloading {pdf_url} → {filename}", file=sys.stderr)
                    resp = await context.request.get(pdf_url)
                    out_path.write_bytes(await resp.body())
                all_fcd.append(filename)
            nxt = page.locator("a#lvFCD_next")
            if "disabled" in (await nxt.get_attribute("class") or ""):
                break
            await nxt.click()
            await page.wait_for_timeout(1000)
        print(f"✅ Downloaded or skipped {len(all_fcd)} financial disclosures for issuer id={id_}", file=sys.stderr)


# Register EMMA-specific scrapers
class EMMAIssueDetailScraper(EMMABaseScraper):
    """Scrape the security table for a given issue ID from EMMA IssueView page."""

    def build_url(self, id: str, **_) -> str:
        return f"https://emma.msrb.org/IssueView/Details/{id}"

    async def parse_and_save(self, page: Page, **kwargs) -> None:
        await page.wait_for_selector("table#dtSecurities tbody tr", timeout=15000)
        rows = await page.locator("table#dtSecurities tbody tr").all()
        securities = []
        for row in rows:
            tds = await row.locator("td").all()
            cusip = await tds[0].locator("img").get_attribute("data-cusip9") or ""
            principal = (await tds[1].inner_text()).strip()
            description = (await tds[2].inner_text()).strip()
            coupon = (await tds[3].inner_text()).strip()
            maturity = (await tds[4].inner_text()).strip()
            price_yield = (await tds[5].inner_text()).strip()
            price = (await tds[6].inner_text()).strip()
            yield_val = (await tds[7].inner_text()).strip()
            ratings = []
            for i in range(8, 12):
                cell = tds[i]
                img = cell.locator("img")
                if await img.count():
                    ratings.append((await img.get_attribute("data-rating")) or "")
                else:
                    ratings.append((await cell.inner_text()).strip())
            securities.append([cusip, principal, description, coupon, maturity, price_yield, price, yield_val] + ratings)
        securities_file = self.out_dir / "securities.csv"
        with open(securities_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "CUSIP", "Principal Amount at Issuance ($)", "Security Description",
                "Coupon", "Maturity Date", "Price/Yield", "Price", "Yield",
                "Fitch", "KBRA", "Moody's", "S&P"
            ])
            writer.writerows(securities)
        print(f"✅ Saved {len(securities)} securities to {securities_file.name}", file=sys.stderr)
SCRAPERS = {
    "security": EMMASecurityDetailScraper,
    "state_issuers": EMMAStateIssuersScraper,
    "issuer_detail": EMMAIssuerDetailScraper,
    "issue_detail": EMMAIssueDetailScraper,
}


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="EMMA (MSRB) municipal bond scraper")
    parser.add_argument("task", choices=SCRAPERS.keys(), help="Which EMMA scrape task to run")
    parser.add_argument("--cusip", help="CUSIP for security/details task")
    parser.add_argument("--state", help="State code (e.g. AK) for state_issuers task")
    parser.add_argument("--all-states", action="store_true",
                        help="Run state_issuers for all states in data/us_states.csv and aggregate into one CSV")
    parser.add_argument("--id", help="Issuer ID for issuer_detail task")
    parser.add_argument("--output-dir", "-o", default="emma_output",
                        help="Base output directory for downloads")
    args = parser.parse_args()

    # validate required parameters per task
    if args.task == "security" and not args.cusip:
        parser.error("security task requires --cusip")
    if args.task == "state_issuers" and not args.state and not args.all_states:
        parser.error("state_issuers task requires --state or --all-states")
    if args.task == "state_issuers" and args.state and args.all_states:
        parser.error("state_issuers task requires either --state or --all-states, not both")
    if args.task == "issuer_detail" and not args.id:
        parser.error("issuer_detail task requires --id")
    if args.task == "issue_detail" and not args.id:
        parser.error("issue_detail task requires --id")
    # aggregate issuers for all states into a single CSV
    if args.task == "state_issuers" and args.all_states:
        base_output = Path(args.output_dir)
        data_file = Path(__file__).parent / 'data' / 'us_states.csv'
        aggregated = []
        scraper = SCRAPERS['state_issuers'](base_output / 'state_issuers')
        for row in csv.DictReader(data_file.open()):
            state = row.get('Abbreviation')
            if not state:
                continue
            print(f'[{state}] Scraping state issuers...', file=sys.stderr)
            rows = await scraper.run(state=state, aggregate=True)
            if rows:
                for rec in rows:
                    aggregated.append([state] + rec)
        out_dir = base_output / 'state_issuers'
        out_dir.mkdir(exist_ok=True, parents=True)
        aggregated_file = out_dir / 'issuers.csv'
        with open(aggregated_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['State', 'Issuer Name', 'Issuer ID', 'Issuer Type'])
            writer.writerows(aggregated)
        print(f"✅ Aggregated {len(aggregated)} issuers to {aggregated_file}", file=sys.stderr)
        return

    base_output = Path(args.output_dir)
    # build output directory hierarchy: base/task/identifier
    out_dir = base_output / args.task
    if args.task == "security":
        out_dir = out_dir / args.cusip
    elif args.task == "state_issuers":
        out_dir = out_dir / args.state
    else:
        out_dir = out_dir / args.id
    scraper = SCRAPERS[args.task](out_dir)

    params: Dict[str, Any] = {}
    if args.task == "security":
        params["cusip"] = args.cusip
    elif args.task == "state_issuers":
        params["state"] = args.state
    elif args.task == "issuer_detail" or args.task == "issue_detail":
        params["id"] = args.id

    await scraper.run(**params)


if __name__ == "__main__":
    asyncio.run(main())
