import boto3
import json
import os
from botocore.exceptions import BotoCoreError, ClientError

from cv_parser import parse_cv_from_s3
from cv_keywords import extract_keywords, upload_keywords_to_s3
from agg_common import secrets_loader

def main():
    # Main function to handle the CV processing and keyword extraction
    try:
        # Load configuration from environment variables from ECS task definition
        bucket_name = os.environ.get("S3_BUCKET")
        object_name = os.environ.get("S3_KEY")

        if not bucket_name or not object_name:
            raise ValueError("S3_BUCKET and S3_KEY environment variables must be set")

        aws_secrets = secrets_loader.get_json_secret("aws/credentials")
        #access_key_id = aws_secrets.get("AWS_ACCESS_KEY_ID")
        #secret_access_key = aws_secrets.get("AWS_SECRET_ACCESS_KEY")
        region = aws_secrets.get("AWS_REGION", "eu-west-1")

        s3_client = boto3.client(
            "s3",
            region_name=region
        )
        print(f"Processing CV from bucket: {bucket_name}, key: {object_name}")
        text = parse_cv_from_s3(s3_client, bucket_name, object_name)
        print(f"Extracted text")
        
        print(f"Extracting keywords...")  
        keywords_list = extract_keywords(text)
        keywords_object_name = f"cv_keywords/{object_name.rsplit('/', 1)[-1].replace('.pdf','_keywords.json')}"
        
        print(f"Uploading keywords to {keywords_object_name} in bucket {bucket_name}...")
        upload_keywords_to_s3(s3_client, bucket_name, keywords_object_name, keywords_list)
        
        print(f"Keywords extracted and uploaded successfully to {keywords_object_name}")
    
    except Exception as e:
        print (f"Error during processing: {e}")
        raise e

if __name__ == "__main__":
    main()

        