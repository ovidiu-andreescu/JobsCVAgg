from typing import List

from .base import Provider
from .remotive import RemotiveProvider
from .adzuna import AdzunaProvider

def available_providers() -> List[Provider]:
    out: List[Provider] = []

    all_provider_instances = [
        RemotiveProvider(),
        AdzunaProvider(),
    ]

    for p in all_provider_instances:
        if p.enabled():
            out.append(p)
    return out
