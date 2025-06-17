import asyncio
import json
import re
from playwright.async_api import async_playwright

async def test_company(page, company):
    name = company["name"]
    selector = company["job_selector"]
    careers_url = company["careers_url"]
    job_url_base = company["job_url_base"]

    if not careers_url:
        print(f"{name} ⚠️ skipped (no careers_url)")
        return

    pattern = re.compile(selector)

    try:
        await page.goto(careers_url, timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=10000)
        await asyncio.sleep(10)  # <-- fixed 10 seconds wait after loading

        links = await page.query_selector_all("a")
        job_count = 0

        for link in links:
            try:
                href = await link.get_attribute("href") or ""
                if not pattern.search(href):
                    continue

                raw_text = (await link.inner_text()).strip()
                if not raw_text:
                    continue
                title = raw_text.splitlines()[0].strip()
                if not title:
                    continue

                job_count += 1
                if job_count >= 2:
                    break
            except:
                continue

        if job_count >= 2:
            print(f"{name} ✅")
        else:
            print(f"{name} ❌ failed on {selector}")

    except Exception:
        print(f"{name} ❌ failed on {selector}")

async def main():
    with open("companies.json", "r") as f:
        companies = json.load(f)

    companies = companies[1:]  # Skip template

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        semaphore = asyncio.Semaphore(5)  # Limit concurrency to 5

        async def run_task(company):
            async with semaphore:
                page = await context.new_page()
                await test_company(page, company)
                await page.close()

        await asyncio.gather(*(run_task(company) for company in companies))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
