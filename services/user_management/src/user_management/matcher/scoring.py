import math
import re
from typing import List, Set, Dict
from .models import JobForScoring, ScoredJob

_WORD = re.compile(r"[a-z0-9+#.-]+")

STOPWORDS = {
    "and","or","of","the","a","an","to","in","for","with","on","at","by","from","as",
    "using","use","used","usage","experience","experiences","skills","skill","strong",
    "good","best","better","great","plus","junior","senior","lead","leading","team",
    "teams","across","around","while","within","over","across","about","more","less",
    "many","some","such","that","this","these","those","will","can","ability","able",
    "work","working","environment","culture","company","role","position","positions",
    "responsibilities","requirements","quality","practice","practices","success",
    "successful","mission","growth","growing","improve","improving","improvement",
    "ensure","ensuring","enable","enabling","support","supporting","help","drive",
    "driving","make","making","deliver","delivering","delivered","develop","developing",
    "developed","design","designing","designed","build","building","built","optimize",
    "optimizing","optimization","maintain","maintaining","maintenance","testing","test",
    "tests","automated","automation","secure","security","reliable","reliability",
    "efficient","efficiency","performance","scalable","scalability","agile","scrum",
    "product","products","applications","application","software","systems","system",
    "domain","data","digital","global","international","patients","customer","clients"
}

ALIASES = {
    "postgresql": "postgres",
    "postgre": "postgres",
    "postgress": "postgres",
    "aws lambda": "aws-lambda",
    "lambda": "aws-lambda",
    "serverless": "aws-lambda",
    "amazon web services": "aws",
    "gcp": "google-cloud",
    "google cloud": "google-cloud",
    "ms sql": "sqlserver",
    "mssql": "sqlserver",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "k8s": "kubernetes",
    "docker compose": "docker-compose",
    "ci/cd": "ci-cd",
    "ci\\cd": "ci-cd",
    "rest": "rest-api",
    "restful": "rest-api",
    "graphql": "graph-ql"
}

def _lemmatize_lite(tok: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if len(tok) > 4 and tok.endswith(suf):
            return tok[: -len(suf)]
    return tok

def _normalize_term(term: str) -> str | None:
    term = term.lower().strip()
    tokens = _WORD.findall(term)
    if not tokens:
        return None
    norm = " ".join(tokens)

    if norm in ALIASES:
        norm = ALIASES[norm]

    parts = []
    for p in norm.split():
        if p in STOPWORDS:
            continue
        p = _lemmatize_lite(p)
        if p and p not in STOPWORDS:
            parts.append(p)

    if not parts:
        return None

    return " ".join(parts)

def _normalize_keywords(keywords: Set[str]) -> Set[str]:
    out: Set[str] = set()
    for k in keywords:
        norm = _normalize_term(k)
        if norm:
            out.add(norm)
    return out

def _build_idf(jobs: List[JobForScoring]) -> Dict[str, float]:
    df: Dict[str, int] = {}
    N = len(jobs) or 1
    for job in jobs:
        norm = _normalize_keywords(job.keywords)
        for t in norm:
            df[t] = df.get(t, 0) + 1
    idf: Dict[str, float] = {}
    for t, d in df.items():
        idf[t] = math.log((N + 1) / (d + 1)) + 1.0
    return idf

def _weighted_jaccard(a: Set[str], b: Set[str], idf: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    inter = a & b
    union = a | b
    w_inter = sum(idf.get(t, 1.0) for t in inter)
    w_union = sum(idf.get(t, 1.0) for t in union)
    if w_union == 0.0:
        return 0.0
    return w_inter / w_union

def calculate_jaccard_score(input_keywords: Set[str], job_keywords: Set[str]) -> float:
    if not input_keywords or not job_keywords:
        return 0.0
    inter = len(input_keywords & job_keywords)
    union = len(input_keywords | job_keywords)
    return (inter / union) if union else 0.0

def score_and_rank_jobs(input_keywords: Set[str], jobs: List[JobForScoring]) -> List[ScoredJob]:
    norm_input = _normalize_keywords(input_keywords)

    idf = _build_idf(jobs)

    scored_jobs: List[ScoredJob] = []
    for job in jobs:
        norm_job = _normalize_keywords(job.keywords)
        score = _weighted_jaccard(norm_input, norm_job, idf)
        if score > 0:
            scored_jobs.append(
                ScoredJob(**job.model_dump(), score=round(score, 3))
            )

    return sorted(scored_jobs, key=lambda j: j.score, reverse=True)