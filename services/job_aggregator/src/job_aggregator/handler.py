import json, asyncio

from .models import Query
from .aggregate import run

def handler(event, _context):
    qsp = (event.get("queryStringParameters") or {}) if isinstance(event, dict) else {}
    body = event.get("body") if isinstance(event, dict) else None

    if isinstance(body, str):
        try: body = json.loads(body or "{}")
        except Exception: body = {}

    q = body.get("q") if isinstance(body, dict) else None
    q = q or qsp.get("q") or event.get("q")  # last-resort

    loc = qsp.get("location") or (body or {}).get("location")
    per_page = int(qsp.get("per_page") or (body or {}).get("per_page") or 50)

    if not q:
        return {"statusCode": 400, "body": json.dumps({"error": "missing q"})}

    jobs = asyncio.run(run(Query(q=q, location=loc, per_page=per_page)))
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": json.dumps([j.model_dump(mode="json") for j in jobs]),
    }