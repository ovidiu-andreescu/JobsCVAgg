# job_aggregator/handler.py

import json, asyncio, sys, os

from .models import Query
from .aggregate import run

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def handler(event, _context):
    qsp = (event.get("queryStringParameters") or {}) if isinstance(event, dict) else {}
    body = event.get("body") if isinstance(event, dict) else None

    if isinstance(body, str):
        try: body = json.loads(body or "{}")
        except Exception: body = {}

    body = body or {}

    q = body.get("q") or qsp.get("q")
    loc = body.get("location") or qsp.get("location")

    try:
        page = int(body.get("page") or qsp.get("page") or 1)
        per_page = int(body.get("per_page") or qsp.get("per_page") or 50)
    except (ValueError, TypeError):
        page = 1
        per_page = 50

    if not q:
        return {"statusCode": 400, "body": json.dumps({"error": "missing q"})}

    query = Query(q=q, location=loc, page=page, results_per_page=per_page)
    jobs = asyncio.run(run(query))

    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps([j.model_dump(mode="json") for j in jobs]),
    }

