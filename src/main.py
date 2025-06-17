import asyncio
import json
import traceback
from dotenv import load_dotenv; load_dotenv()
from scraper import scrape_jobs, compile_patterns
from cache import ensure_table, is_job_cached, cache_job, clean_old_jobs
from sns import DiscordNotifier
import os

CONCURRENT_LIMIT = 5  # Max concurrent scraping tasks

async def scrape_company(company, include_patterns, exclude_patterns, notifier, job_queue):
    try:
        results = await scrape_jobs(company, True, include_patterns, exclude_patterns)
        if results:
            for title, url in results:
                if await is_job_cached(url):
                    print(f"Skipping cached job: {title} @ {company['name']}")
                    continue
                await job_queue.put((title, company['name'], url))
        else:
            print("No jobs due to filters\n")
    except Exception:
        print(f"Error scraping {company['name']}")
        traceback.print_exc()

async def scrape_company_limited(semaphore, company, include_patterns, exclude_patterns, notifier, job_queue):
    async with semaphore:
        await scrape_company(company, include_patterns, exclude_patterns, notifier, job_queue)

async def notifier_worker(notifier, job_queue):
    printed_companies = set()
    while True:
        title, company_name, url = await job_queue.get()

        if company_name not in printed_companies:
            print(f"Checking {company_name}:")
            printed_companies.add(company_name)

        message = f"{title} @ {company_name}\n<{url}>\n"
        print(message)

        if notifier:
            await notifier.send_notification(message)

        await cache_job(title, company_name, url)
        await asyncio.sleep(0.2)  # Standard delay unless rate-limited
        job_queue.task_done()

async def run_scraper():
    try:
        clean_old_jobs(45)
        await ensure_table()

        with open("companies.json", "r") as f:
            companies = json.load(f)[1:]  # Skip template

        include_patterns, exclude_patterns = compile_patterns()

        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        notifier = DiscordNotifier(webhook_url) if webhook_url else None
        if not webhook_url:
            print("Warning: DISCORD_WEBHOOK_URL not set in environment. Notifications disabled.")

        job_queue = asyncio.Queue()
        notifier_task = asyncio.create_task(notifier_worker(notifier, job_queue))

        semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)

        scrape_tasks = [
            asyncio.create_task(scrape_company_limited(semaphore, company, include_patterns, exclude_patterns, notifier, job_queue))
            for company in companies
        ]

        await asyncio.gather(*scrape_tasks)

        await job_queue.join()

        notifier_task.cancel()
        try:
            await notifier_task
        except asyncio.CancelledError:
            pass

    except Exception:
        print("Failed to load companies or encountered major error.")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_scraper())
