# job_aggregator/dedupe.py

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit
from typing import Iterable, List, Tuple
from .models import Job

def _norm_url(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path.rstrip("/"), "", ""))

def signature(j: Job) -> Tuple[str, str, str | None]:
    return _norm_url(str(j.url)) or "", j.title.lower().strip(), (j.company or "").lower().strip() or None

def dedupe(jobs: Iterable[Job]) -> List[Job]:
    seen: set[Tuple[str, str, str | None]] = set()
    out: List[Job] = []
    for j in jobs:
        sig = signature(j)
        if sig in seen:
            continue
        seen.add(sig)
        out.append(j)
    return out
