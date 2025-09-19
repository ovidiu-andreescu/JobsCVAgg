# job_aggregator/storage.py


import boto3
import os
from typing import List
from .models import Job

table_name = os.environ.get('JOBS_TABLE_NAME')
if not table_name:
    raise ValueError("Missing required environment variable: JOBS_TABLE_NAME")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)

def save_jobs(jobs: List[Job]):
    if not jobs:
        print("No jobs to save.")
        return

    print(f"Attempting to save {len(jobs)} jobs to table '{table}'...")
    try:
        with table.batch_writer() as batch:
            for job in jobs:
                item_dict = job.model_dump(mode="json")

                if 'keywords' in item_dict and not item_dict['keywords']:
                    del item_dict['keywords']

                batch.put_item(Item=item_dict)
        print(f"[info] Successfully initiated batch write for {len(jobs)} jobs.")
    except Exception as e:
        raise e
