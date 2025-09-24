import boto3, os, json
from typing import List, Set, Optional

from .models import JobForScoring

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

JOBS_TABLE_NAME = os.environ['JOBS_TABLE_NAME']
CV_BUCKET = os.environ['CV_S3_BUCKET']

jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

def _read_keywords(key: str) -> Set[str]:
    try:
        obj = s3.get_object(Bucket=CV_BUCKET, Key=key)
        data = json.loads(obj["Body"].read())
        return set(data) if isinstance(data, list) else set()
    except s3.exceptions.NoSuchKey:
        return set()
    except Exception as e:
        print(f"[warn] read failed {key}: {e}")
        return set()


def get_cv_keywords_from_s3(email: str) -> Set[str]:
    email = email.strip().lower()

    prefix = f"cv_keywords/{email}/"
    try:
        paginator = s3.get_paginator("list_objects_v2")
        latest_key, latest_ts = None, None
        for page in paginator.paginate(Bucket=CV_BUCKET, Prefix=prefix):
            for o in page.get("Contents", []):
                if o["Key"].endswith("_keywords.json"):
                    ts = o["LastModified"]
                    if latest_ts is None or ts > latest_ts:
                        latest_ts, latest_key = ts, o["Key"]
        if latest_key:
            return _read_keywords(latest_key)
    except Exception as e:
        print(f"[warn] listing {prefix} failed: {e}")

    legacy = f"cv_keywords/{email}_keywords.json"
    kws = _read_keywords(legacy)
    if kws:
        return kws

    print(f"[info] No keywords found for {email} in {CV_BUCKET}")
    return set()

def get_all_jobs_for_scoring() -> List[JobForScoring]:
    # unchanged from your original storage; scans Jobs table and maps to JobForScoring
    resp = jobs_table.scan(
        ProjectionExpression="source, source_job_id, title, company, #u, keywords",
        ExpressionAttributeNames={"#u": "url"},
    )
    items = resp.get("Items", [])
    return [JobForScoring(**it) for it in items]