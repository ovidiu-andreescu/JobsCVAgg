# providers/remotive

import httpx

from typing import List
from .base import Provider
from job_aggregator.models import Job, Query
from datetime import datetime

API = "https://remotive.com/api/remote-jobs"

def _parse_dt(s: str | None) -> datetime | None:
    if not s: return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None

class RemotiveProvider(Provider):
    name = "remotive"

    async def search(self, query: Query) -> List[Job]:
        params = {"search": query.q}

        if query.location:
            params["category"] = query.location

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(API, params=params)
            r.raise_for_status()
            data = r.json()

        jobs: List[Job] = []
        for item in data.get("jobs", []):
            job_id = item.get("id")
            if not job_id:
                continue

            jobs.append(Job(
                source=self.name,
                source_job_id=str(job_id),
                title=(item.get("title") or "").strip(),
                company=item.get("company_name"),
                location=item.get("candidate_required_location"),
                remote=True,
                url=item.get("url"),
                description=item.get("description"),
                posted_at=_parse_dt(item.get("publication_date")),
                salary=item.get("salary"),
            ))

        return jobs

