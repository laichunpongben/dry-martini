#!/usr/bin/env python3
import sys
import os
import asyncio
import urllib.parse
import random
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from utils.http_helper import USER_AGENTS
from utils.logging_helper import logger
from utils.pdf_helper import extract_text_from_pdf

# ─── Configuration ─────────────────────────────────────────────────────────────
DEBUG_DIR = Path("debug_artifacts")
DEBUG_DIR.mkdir(exist_ok=True)
SEARCH_TIMEOUT = 15_000  # ms
PDF_TIMEOUT    = 15_000  # ms
PDF_EXT        = re.compile(r'\.pdf($|\?)', re.IGNORECASE)
PDF_REGEX      = re.compile(r'https?://[^\s"\'<>]+\.pdf', re.IGNORECASE)

# Bond-specific keywords for verification
KEYWORDS = [
    "prospectus",
    "coupon rate",
    "maturity date",
    "use of proceeds",
    "risk factors",
    "underwriter",
    "trustee",
    "credit rating"
]
MIN_KEYWORD_MATCHES = 3

def is_bond_prospectus(text: str, min_matches: int = MIN_KEYWORD_MATCHES) -> bool:
    """Return True if at least `min_matches` bond keywords appear in the text."""
    lower = text.lower()
    matches = sum(1 for kw in KEYWORDS if kw in lower)
    return matches >= min_matches


async def save_debug(page, prefix: str):
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    html_path = DEBUG_DIR / f"{prefix}_{ts}.html"
    png_path  = DEBUG_DIR / f"{prefix}_{ts}.png"

    html = await page.content()
    html_path.write_text(html, encoding="utf-8")
    logger.debug(f"Saved debug HTML: {html_path}")

    await page.screenshot(path=str(png_path), full_page=True)
    logger.debug(f"Saved debug screenshot: {png_path}")


class Scout:
    """Google-search helper with built-in PDF-link fallback and debug capture."""

    def __init__(self, headless: bool = True):
        self.headless   = headless
        self.playwright = None
        self.browser    = None
        self.context    = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        ua = random.choice(USER_AGENTS)
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        self.context = await self.browser.new_context(
            user_agent=ua,
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True
        )
        logger.debug(f"Scout started with UA={ua}")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.context:    await self.context.close()
        if self.browser:    await self.browser.close()
        if self.playwright: await self.playwright.stop()
        logger.debug("Scout shutdown complete")

    async def google_search(self, query: str, max_results=5, retries=2) -> List[Dict[str,str]]:
        enc = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={enc}&num={max_results}"
        for attempt in range(1, retries+1):
            page = await self.context.new_page()
            page.set_default_timeout(SEARCH_TIMEOUT)
            try:
                logger.debug(f"[Search] Attempt {attempt} → {url}")
                await page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(1, 2))

                results: List[Dict[str,str]] = []
                # Organic results
                loc = page.locator("div#search div.g a>h3")
                count = await loc.count()
                for i in range(count):
                    if len(results) >= max_results: break
                    title = await loc.nth(i).inner_text()
                    href  = await loc.nth(i).locator("..").get_attribute("href")
                    if href and href.startswith("http"):
                        results.append({"title": title, "url": href})

                # Fallback: any .pdf in raw HTML
                if len(results) < max_results:
                    html = await page.content()
                    for m in PDF_REGEX.findall(html):
                        if len(results) >= max_results: break
                        if any(r["url"] == m for r in results): continue
                        results.append({"title": os.path.basename(m), "url": m})

                await save_debug(page, f"search_attempt{attempt}")
                await page.close()

                if results:
                    return results

            except PlaywrightTimeoutError as e:
                logger.warning(f"[Search] Timeout #{attempt}: {e}")
                await save_debug(page, f"search_timeout{attempt}")
                await page.close()
            except Exception as e:
                logger.error(f"[Search] Error #{attempt}: {e}")
                await save_debug(page, f"search_error{attempt}")
                await page.close()

            await asyncio.sleep(1)

        # Final debug capture
        page = await self.context.new_page()
        page.set_default_timeout(5_000)
        try:
            await page.goto(url, wait_until="domcontentloaded")
        except Exception:
            pass
        await save_debug(page, "search_final_failure")
        await page.close()

        logger.error("[Search] No results after retries")
        return []


async def find_and_download(isin: str, output_folder: str = "."):
    logger.info(f"Starting prospectus download for ISIN={isin}")
    output_path = Path(output_folder) / f"{isin}-prospectus.pdf"

    # 1) Gather candidate URLs
    async with Scout() as scout:
        candidates = await scout.google_search(f"{isin} prospectus pdf", max_results=5, retries=2)

    if not candidates:
        logger.error("No search results; aborting")
        return

    # 2) Process each candidate
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))

        for idx, cand in enumerate(candidates, start=1):
            url = cand["url"]
            logger.info(f"[{idx}/{len(candidates)}] Candidate URL: {url}")

            # Direct-PDF URL?
            if PDF_EXT.search(url):
                logger.debug(" → Direct-PDF URL detected")
                try:
                    resp = await context.request.get(url, timeout=PDF_TIMEOUT)
                    if not resp.ok:
                        logger.warning(f"HTTP {resp.status}; skipping")
                    else:
                        pdf_bytes = await resp.body()
                        #  tmp file not strictly needed here since we have bytes,
                        #  but naming underscores the idea
                        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                            tmp.write(pdf_bytes)
                            tmp_path = tmp.name

                        text = await extract_text_from_pdf(pdf_bytes) or ""
                        if is_bond_prospectus(text):
                            os.replace(tmp_path, output_path)
                            logger.info(f"✅ Saved prospectus to {output_path}")
                            await context.close(); await browser.close()
                            return
                        else:
                            logger.debug("    Verification failed; discarding")
                            os.remove(tmp_path)
                except Exception as e:
                    logger.error(f"    Error downloading/parsing PDF: {e}")
                continue

            # HTML page: find embedded PDF links
            page = await context.new_page()
            page.set_default_timeout(SEARCH_TIMEOUT)
            try:
                await page.goto(url, wait_until="domcontentloaded")
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout loading page: {url}")
                await save_debug(page, f"load_{idx}")
                await page.close()
                continue

            hrefs = await page.locator("a").evaluate_all(
                "els => els.map(a=>a.href).filter(h=>h&&h.toLowerCase().endswith('.pdf'))"
            )
            logger.debug(f" → Found {len(hrefs)} PDF link(s) on page")

            for pdf_href in hrefs:
                logger.info(f"   ▶ Trying PDF: {pdf_href}")
                try:
                    resp = await page.request.get(pdf_href, timeout=PDF_TIMEOUT)
                    if not resp.ok:
                        logger.debug(f"    HTTP {resp.status}; skip")
                        continue

                    pdf_bytes = await resp.body()
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        tmp.write(pdf_bytes)
                        tmp_path = tmp.name

                    text = await extract_text_from_pdf(pdf_bytes) or ""
                    if is_bond_prospectus(text):
                        os.replace(tmp_path, output_path)
                        logger.info(f"✅ Saved prospectus to {output_path}")
                        await page.close(); await context.close(); await browser.close()
                        return
                    else:
                        logger.debug("    Verification failed; discarding")
                        os.remove(tmp_path)

                except Exception as e:
                    logger.error(f"    Error processing PDF: {e}")
                    await save_debug(page, f"pdf_{idx}")
            await page.close()

        await context.close()
        await browser.close()
        logger.error("❌ No matching prospectus PDF found")


def main():
    if len(sys.argv) < 2:
        print("Usage: scout.py <ISIN> [output_folder]")
        sys.exit(1)

    isin = sys.argv[1].strip().upper()
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(outdir, exist_ok=True)

    asyncio.run(find_and_download(isin, outdir))


if __name__ == "__main__":
    main()
