from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from job_aggregator.models import Query, Job

class Provider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: Query) -> List[Job]: ...

    def enabled(self) -> bool:
        return True