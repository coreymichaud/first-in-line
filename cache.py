import json
import os
from typing import List
from datetime import datetime, timedelta

CACHE_FILE = "cache.json"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"  # ISO-like format without timezone

async def ensure_table():
    # No database, so nothing to ensure here
    return

def load_cache() -> List[dict]:
    if not os.path.exists(CACHE_FILE):
        return []
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        # File exists but is empty or corrupted, treat as empty cache
        return []

def save_cache(cache: List[dict]):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

async def is_job_cached(url: str) -> bool:
    cache = load_cache()
    return any(job["url"] == url for job in cache)

async def cache_job(title: str, company: str, url: str):
    cache = load_cache()
    if not any(job["url"] == url for job in cache):
        now_str = datetime.utcnow().strftime(DATE_FORMAT)
        cache.append({
            "title": title,
            "company": company,
            "url": url,
            "cached_at": now_str  # store time added in UTC
        })
        save_cache(cache)

def clean_old_jobs(days: int = 45):
    """Remove jobs cached more than `days` ago."""
    cache = load_cache()
    cutoff = datetime.utcnow() - timedelta(days=days)
    new_cache = []
    for job in cache:
        cached_at_str = job.get("cached_at")
        if cached_at_str:
            try:
                cached_at = datetime.strptime(cached_at_str, DATE_FORMAT)
                if cached_at >= cutoff:
                    new_cache.append(job)
            except Exception:
                # If parsing fails, keep the job just in case
                new_cache.append(job)
        else:
            # No cached_at timestamp, keep by default
            new_cache.append(job)
    if len(new_cache) != len(cache):
        save_cache(new_cache)
