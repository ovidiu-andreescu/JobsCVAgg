from typing import List, Set
from .models import JobForScoring, ScoredJob

def calculate_jaccard_score(input_keywords: Set[str], job_keywords: Set[str]) -> float:
    if not input_keywords or not job_keywords:
        return 0.0

    intersection_size = len(input_keywords.intersection(job_keywords))
    union_size = len(input_keywords.union(job_keywords))

    if union_size == 0:
        return 0.0

    return intersection_size / union_size

def score_and_rank_jobs(input_keywords: Set[str], jobs: List[JobForScoring]) -> List[ScoredJob]:
    scored_jobs = []
    for job in jobs:
        score = calculate_jaccard_score(input_keywords, job.keywords)

        if score > 0:
            scored_job = ScoredJob(**job.model_dump(), score=round(score, 3))
            scored_jobs.append(scored_job)

    return sorted(scored_jobs, key=lambda j: j.score, reverse=True)

