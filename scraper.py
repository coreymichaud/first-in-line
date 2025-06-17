import re
import asyncio
from playwright.async_api import async_playwright

# Title filtering
def compile_patterns():
    include_title = [
        r'\bjunior\b', r'\bjr\.?\b', r'\banalyst\b',
        r'\bdata\b', r'\bassociate\b', r'\bentry-level\b',
        r'\bai\b', r'\bml\b', r'\bassistant\b', r'\b1\b', r'\bi\.?\b'
    ]
    exclude_title = [
        r'\bsenior\b', r'\bsr\.?\b', r'\blead\b', r'\bmanager\b', r'\bhead\b',
        r'\bpresident\b', r'\bvice\b', r'\bvp\b',
        r'\bdirector\b', r'\bprincipal\b', r'\bstaff\b', r'\bretail\b', r'\bguard\b',
        r'\bclient\b', r'\bmaster\b', r'\bdistinguished\b', r'\bchief\b', r'\bios\b',
        r'\bactuarial\b', r'\bpatient\b', r'\bnurse\b'
    ]
    return (
        [re.compile(p, re.IGNORECASE) for p in include_title],
        [re.compile(p, re.IGNORECASE) for p in exclude_title]
    )

def is_title_valid(title, filter_enabled, include_patterns, exclude_patterns):
    if not filter_enabled:
        return True
    include_match = any(p.search(title) for p in include_patterns)
    exclude_match = any(p.search(title) for p in exclude_patterns)
    return include_match and not exclude_match

async def scrape_jobs(company, filter_enabled=True, include_patterns=None, exclude_patterns=None):
    results = []
    seen_links = set()

    if not company.get("careers_url"):
        return results

    pattern = re.compile(company["job_selector"])
    letter_pattern = re.compile(r'[A-Za-z]')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(company["careers_url"], wait_until="domcontentloaded")
        await asyncio.sleep(10)

        links = await page.query_selector_all("a")
        for link in links:
            try:
                href = await link.get_attribute("href") or ""
                if not href or not pattern.search(href) or href in seen_links:
                    continue

                seen_links.add(href)

                raw_text = await link.inner_text()
                lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
                title = None

                # Special title logic for specific companies
                if company.get("name") in ["IBM", "Spectrum", "Discord"]:
                    if len(lines) > 1 and letter_pattern.search(lines[1]):
                        title = lines[1]
                else:
                    title = next((line for line in lines if letter_pattern.search(line)), None)

                if not title:
                    title = (await link.get_attribute("aria-label") or "").strip()

                if not title:
                    continue

                # Normalize title for comparison
                title_lower = title.lower()

                # Skipping based on title
                if company.get("name") == "First Citizens Bank" and title_lower in ["apply now", "refer"]:
                    continue

                if not is_title_valid(title, filter_enabled, include_patterns, exclude_patterns):
                    continue

                full_link = href if not company["job_url_base"] else company["job_url_base"] + href
                results.append((title, full_link))

            except Exception:
                continue

        await browser.close()

    return results
