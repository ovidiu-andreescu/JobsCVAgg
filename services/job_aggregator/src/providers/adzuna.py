# providers/adzuna.py

import os, httpx

from datetime import datetime
from typing import List
from job_aggregator import config
from job_aggregator.models import Job, Query
from .base import Provider

ADZUNA_BASE = os.getenv("ADZUNA_API_BASE", "https://api.adzuna.com/v1/api/jobs")

def _country() -> str:
    return os.getenv("ADZUNA_COUNTRY", "ro").lower()

def _endpoint(page: int, country: str | None = None) -> str:
    c = (country or _country()).lower()
    return f"{ADZUNA_BASE}/{c}/search/{page}"

def _parse_dt(s: str | None):
    if not s: return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

class AdzunaProvider(Provider):
    name = "adzuna"

    def __init__(self, *, country: str | None = None):
        self.country = country

    def enabled(self) -> bool:
        return bool(config.adzuna_app_id() and config.adzuna_app_key())

    async def search(self, query: Query) -> List[Job]:
        app_id = config.adzuna_app_id()
        app_key = config.adzuna_app_key()

        url = _endpoint(page=query.page or 1, country=self.country)
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": query.results_per_page,
            "what": query.q,
            "content-type": "application/json"
        }

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        jobs: List[Job] = []
        for item in data.get("results", []):
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary_str = ""
            if salary_min and salary_max:
                salary_str = f"{salary_min} - {salary_max}"
            elif salary_min:
                salary_str = str(salary_min)

            jobs.append(Job(
                source=self.name,
                source_job_id=str(item["id"]),
                title=(item["title"] or "").strip(),
                company=(item["company"] or {}).get("display_name"),
                location=(item["location"] or {}).get("display_name"),
                remote = None,
                url = item.get("redirect_url"),
                description = item.get("description"),
                posted_at = _parse_dt(item.get("created")),
                salary=salary_str,
                extras={"category": (item.get("category") or {}).get("label"),}
            ))

        return jobs