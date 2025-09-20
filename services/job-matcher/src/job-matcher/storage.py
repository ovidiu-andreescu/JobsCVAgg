import boto3, os, json
from typing import List, Set

from .models import JobForScoring

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

JOBS_TABLE_NAME = os.environ['JOBS_TABLE_NAME']
CV_KEYWORDS_BUCKET_NAME = os.environ['CV_KEYWORDS_BUCKET_NAME']

jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

def get_cv_keywords_from_s3(user_id: str) -> Set[str]:
    object_key = f"cv_keywords/{user_id}_keywords.json"
    print(f"[info] Fetching CV keywords for user '{user_id}' from s3://{CV_KEYWORDS_BUCKET_NAME}/{object_key}")

    try:
        response = s3_client.get_object(Bucket=CV_KEYWORDS_BUCKET_NAME, Key=object_key)
        json_content = response['Body'].read()
        keywords_list = json.loads(json_content)

        if not isinstance(keywords_list, list):
            print(f"[warn] S3 object for user '{user_id}' is not a valid JSON list.")
            return set()

        return set(keywords_list)
    except s3_client.exceptions.NoSuchKey:
        print(f"[warn] No keywords file found for user '{user_id}' at s3://{CV_KEYWORDS_BUCKET_NAME}/{object_key}")
        return set()
    except Exception as e:
        print(f"[ERROR] Failed to get or parse keywords from S3 for user '{user_id}': {e}")
        return set()


def get_all_jobs_for_scoring() -> List[JobForScoring]:
    print(f"[info] Scanning table '{JOBS_TABLE_NAME}' for all jobs...")
    response = jobs_table.scan(
        ProjectionExpression="source, source_job_id, title, company, #u, keywords",
        ExpressionAttributeNames={"#u": "url"}
    )
    items = response.get('Items', [])
    print(f"[info] Found {len(items)} jobs to score.")
    return [JobForScoring(**item) for item in items]
