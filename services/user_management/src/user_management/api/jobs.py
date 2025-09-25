import os
from typing import Any, Dict, List, Optional, Tuple

import boto3
from boto3.dynamodb.conditions import Attr, Or
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/jobs", tags=["jobs"])

_dynamo = boto3.resource("dynamodb")
_JOBS_TABLE = os.environ.get("JOBS_TABLE_NAME")
if not _JOBS_TABLE:
    raise RuntimeError("JOBS_TABLE_NAME env var is required")
_table = _dynamo.Table(_JOBS_TABLE)

def _normalize_location(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.strip()
    return s if s else None

def _is_remote(loc: Optional[str]) -> bool:
    return (loc or "").strip().lower() == "remote"

def _build_filter(keywords: Optional[str], location: Optional[str]):
    f = None

    if keywords and keywords.strip():
        tokens = [t.strip() for t in keywords.replace(",", " ").split() if t.strip()]
        kw_exprs = []
        for t in tokens:
            # contains works for String, List, and Set in DynamoDB
            kw_exprs.append(Attr("keywords").contains(t.lower()))
            kw_exprs.append(Attr("title").contains(t))
            kw_exprs.append(Attr("company").contains(t))
        if kw_exprs:
            f = kw_exprs[0]
            for e in kw_exprs[1:]:
                f = Or(f, e)

    if location and not _is_remote(location):
        loc_expr = Attr("location").contains(location)
        f = loc_expr if f is None else Or(f, loc_expr)

    return f

def _scan_with_filter(FilterExpression, Limit: int = 1000):
    items: List[Dict[str, Any]] = []
    kwargs: Dict[str, Any] = {"Limit": min(Limit, 1000)}
    if FilterExpression is not None:
        kwargs["FilterExpression"] = FilterExpression

    while True:
        resp = _table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp or len(items) >= Limit:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return items[:Limit]

@router.get("")
def list_jobs(
    keywords: Optional[str] = Query(None, description="e.g. 'python, fastapi'"),
    location: Optional[str] = Query(None, description="'Bucharest, RO' or 'Remote'"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    try:
        location = _normalize_location(location)
        filt = _build_filter(keywords, location)

        superset_limit = max(per_page * page, 200)
        rows = _scan_with_filter(filt, Limit=superset_limit)

        def to_view(it: Dict[str, Any]) -> Dict[str, Any]:
            src = it.get("source")
            sid = it.get("source_job_id")
            return {
                "id": f"{src}:{sid}" if src and sid else it.get("id") or sid or src,
                "title": it.get("title"),
                "company": it.get("company"),
                "location": it.get("location") or ("Remote" if _is_remote(location) else None),
                "url": it.get("url"),
                "source": src,
                "posted_at": it.get("posted_at"),
            }

        total = len(rows)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = [to_view(it) for it in rows[start:end]]

        return {"items": page_items, "total": total}
    except Exception as e:
        print(f"[jobs] {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail="jobs_list_failed")
