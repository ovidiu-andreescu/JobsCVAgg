import boto3
import json
from botocore.exceptions import BotoCoreError, ClientError

from cv_parser import parse_cv_from_s3
from cv_keywords import extract_keywords, upload_keywords_to_s3
from libs.common.src.agg_common import secrets_loader

def lambda_handler_keywords(event, context):
    try:
        s3_event = event['Records'][0]['s3']
        bucket_name = s3_event['bucket']['name']
        object_name = s3_event['object']['key']

        aws_secrets = secrets_loader.get_json_secret("aws/credentials")
        access_key_id = aws_secrets.get("AWS_ACCESS_KEY_ID")
        secret_access_key = aws_secrets.get("AWS_SECRET_ACCESS_KEY")
        region = aws_secrets.get("AWS_REGION", "eu-central-1")

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )

        text = parse_cv_from_s3(s3_client, bucket_name, object_name)

        keywords_list = extract_keywords(text)
        keywords_object_name = f"cv_keywords/{object_name.rsplit('/', 1)[-1].replace('.pdf','_keywords.json')}"
        upload_keywords_to_s3(s3_client, bucket_name, keywords_object_name, keywords_list)

        return {
            'statusCode': 200,
            'body': json.dumps({
                "message": "Keywords extracted and uploaded successfully",
                "keywords_file": keywords_object_name
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                "error": str(e)
            })
        }


        