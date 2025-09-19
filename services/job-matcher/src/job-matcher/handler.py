import json
from typing import Dict, Any
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .storage import get_all_jobs_for_scoring, get_cv_keywords_from_s3
from .scoring import score_and_rank_jobs


def handler(event: Dict, _context):
    try:
        user_id = event['pathParameters']['user_id']
        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"error": "user_id in path cannot be empty"})}

        print(f"[info] Starting match process for user_id: {user_id}")

        cv_keywords = get_cv_keywords_from_s3(user_id)
        all_jobs = get_all_jobs_for_scoring()

        if not cv_keywords:
            return {"statusCode": 404, "body": json.dumps({"error": f"No CV keywords found for user {user_id}"})}

        recommendations = score_and_rank_jobs(cv_keywords, all_jobs)
        response_body = [job.model_dump(mode="json") for job in recommendations[:50]]

        return {
            "statusCode": 200,
            "headers": {"content-type": "application/json"},
            "body": json.dumps(response_body),
        }

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal server error"})}