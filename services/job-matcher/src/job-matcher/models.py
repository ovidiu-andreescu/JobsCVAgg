from pydantic import BaseModel, Field
from typing import List, Set, Optional

class MatchRequest(BaseModel):
    keywords: List[str] = Field(default_factory=list)

class JobForScoring(BaseModel):
    source: str
    source_job_id: str
    title: str
    company: Optional[str] = None
    url: str
    keywords: Set[str] = Field(default_factory=set)

class ScoredJob(JobForScoring):
    score: float = 0.0
