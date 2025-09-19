# job_aggregator/aggregate.py
from __future__ import annotations

import asyncio, httpx, sys, os

from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .models import Job, Query
from providers import available_providers
from .dedupe import dedupe
from .storage import save_jobs


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def extract_keywords(text: str | None) -> set:
    if not text:
        return set()
    words = {word.lower() for word in text.split() if len(word) > 3 and word.isalpha()}
    return words

@retry(wait=wait_exponential(min=0.5, max=4), stop=stop_after_attempt(3),
       retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)))
async def _run_provider(p, query: Query) -> List[Job]:
    return await p.search(query)

async def run(query: Query) -> List[Job]:
    providers = available_providers()
    tasks = [asyncio.create_task(_run_provider(p, query)) for p in providers]
    results: List[Job] = []
    for coro in asyncio.as_completed(tasks):
        try:
            results.extend(await coro)
        except Exception as e:
            print(f"[warn] provider failed: {e}")

    unique_jobs = dedupe(results)

    for job in unique_jobs:
        job.keywords = extract_keywords(job.description)

    if unique_jobs:
        try:
            save_jobs(unique_jobs)
            print(f"[info] Successfully saved {len(unique_jobs)} jobs to DynamoDB.")
        except Exception as e:
            print(f"[ERROR] Failed to save jobs to DynamoDB: {e}")

    return unique_jobs