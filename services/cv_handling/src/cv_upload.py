import boto3
import os
import base64
import json
from botocore.exceptions import BotoCoreError, ClientError
from libs.common.src.agg_common import secrets_loader

def upload_cv_to_s3(s3_client, file_path: str, bucket_name: str, object_name: str) -> str:
    """
    Arguments:
    - s3_client: Boto3 S3 client
    - file_path: Local path to the PDF with the CV
    - bucket_name: S3 bucket name
    - object_name: S3 object key (filename in the bucket)
    Returns:
    - presigned URL valid for 1 hour
    Raises:
    - RuntimeError on failure (hope not)
    """
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

def lambda_handler_upload(event, context):
    try:
        # Extracts file data from the event
        file_data = event['body']
        if event.get('isBase64Encoded'): # If the data is base64-encoded, decode it
            file_data = base64.b64decode(file_data)
        # Saves the file temporarily in /tmp
        file_name = event['headers'].get('X-File-Name', 'uploaded_cv.pdf') 
        file_path = f"/tmp/{file_name}"
        with open(file_path, 'wb') as f: # Write the binary data to a file
            f.write(file_data)

        # Loads AWS credentials and S3 bucket name from secrets manager
        aws_secrets = secrets_loader.get_json_secret("aws/credentials")
        #access_key_id = aws_secrets.get("AWS_ACCESS_KEY_ID")
        #secret_access_key = aws_secrets.get("AWS_SECRET_ACCESS_KEY")
        region = aws_secrets.get("AWS_REGION", "eu-west-1")
        bucket_name = aws_secrets.get("CV_S3_BUCKET")

        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            region_name=region
        )

        # Uploads the file to S3 and gets a presigned URL
        object_name = f"cv_uploads/{file_name}"
        presigned_url = upload_cv_to_s3(s3_client, file_path, bucket_name, object_name)
        # Cleans up the temporary file
        os.remove(file_path)
        # Returns the presigned URL in the response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File uploaded successfully',
                'presigned_url': presigned_url
            })
        }
    # Catches any exceptions and returns an error response
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

