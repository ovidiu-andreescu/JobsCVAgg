from typing import List

from .base import Provider
from .remotive import RemotiveProvider
from .adzuna import AdzunaProvider

def available_providers() -> List[Provider]:
    out: List[Provider] = []
    for p in (RemotiveProvider(), AdzunaProvider()):
        if p.enabled:
            out.append(p)
    return out