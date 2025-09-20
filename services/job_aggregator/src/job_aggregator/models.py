# job_aggregator/models.py

from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Any, Set


class Job(BaseModel):
    source: str
    source_job_id: str
    title: str
    company: str
    location: Optional[str]
    remote: Optional[bool] = None
    url: HttpUrl
    description: Optional[str] = None
    keywords: Optional[Set[str]] = None
    salary: Optional[str] = None
    posted_at: Optional[datetime] = None
    extras: dict[str, Any] = Field(default_factory=dict)

class Query(BaseModel):
    q: str
    location: Optional[str] = None
    remote: Optional[bool] = None
    page: Optional[int] = 1
    results_per_page: Optional[int] = 50
