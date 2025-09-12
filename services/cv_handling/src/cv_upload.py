import boto3
import os
from botocore.exceptions import BotoCoreError, ClientError
from libs.common.src.agg_common import secrets_loader

def upload_cv_to_s3(file_path: str, bucket_name: str, object_name: str) -> str:
    """
    Arguments:
    - file_path: Local path to the PDF with the CV
    - bucket_name: S3 bucket name
    - object_name: S3 object key (filename in the bucket)
    Returns:
    - presigned URL valid for 1 hour
    Raises:
    - RuntimeError on failure (hope not)
    """

    # Loads AWS credentials from secrets manager
    aws_secrets = secrets_loader.get_json_secret("aws/credentials")
    access_key_id = aws_secrets.get("AWS_ACCESS_KEY_ID")
    secret_access_key = aws_secrets.get("AWS_SECRET_ACCESS_KEY")
    region = aws_secrets.get("AWS_REGION", "eu-central-1")

    # Initialize S3 client
    s3_client = boto3.client(
        "s3",
        aws_access_key_id = access_key_id,
        aws_secret_access_key = secret_access_key,
        region_name = region
    )

    # Uploads the file
    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed uploading file to S3: {e}")

    # Generates a presigned URL valid for 1 hour
    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params = {'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn = 3600
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed generating presigned URL: {e}")

    return presigned_url 