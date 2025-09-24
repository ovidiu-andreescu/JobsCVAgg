from pathlib import Path
import boto3
from boto3.dynamodb.conditions import Attr, Key
import os
import base64
import json
from botocore.exceptions import BotoCoreError, ClientError
from agg_common import secrets_loader
import logging
from .cv_parser import parse_cv_from_s3
from .cv_keywords import extract_keywords, upload_keywords_to_s3
from urllib.parse import unquote_plus

dynamodb = boto3.resource('dynamodb')

USERS_TABLE = os.getenv("USERS_TABLE_NAME")
_table = dynamodb.Table(USERS_TABLE) if USERS_TABLE else None
USERS_GSI_VERIFY_TOKEN = os.getenv("USERS_GSI_VERIFY_TOKEN", "users_by_verify_token")  # optional

log = logging.getLogger()
log.setLevel(logging.INFO)

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

def _update_user_with_cv_keys(token: str, cv_key: str, kw_key: str) -> bool:
    if not USERS_TABLE:
        return False

    ddb = boto3.resource("dynamodb")
    table = ddb.Table(USERS_TABLE)

    email = None
    try:
        resp = table.query(
            IndexName = USERS_GSI_VERIFY_TOKEN,
            KeyConditionExpression = Key("verify_token").eq(token),
            Limit = 1
        )
        items = resp.get("Items", [])

        if items:
            email = items[0]["email"].lower()

    except Exception as e:
        log.info(f"GSI '{USERS_GSI_VERIFY_TOKEN}' not used ({e}). Falling back to Scan.")

    if not email:
        resp = table.scan(FilterExpression=Attr("verify_token").eq(token))
        items = resp.get("Items", [])
        if not items:
            return False
        email = items[0]["email"].lower()

    table.update_item(
        Key={"email": email},
        UpdateExpression="SET cv_pdf_key = :cv, cv_keywords_key = :kw",
        ExpressionAttributeValues={":cv": cv_key, ":kw": kw_key},
    )

    return True


def set_cv_keys_by_email(email: str, cv_key: str, kw_key: str) -> bool:
    if not email:
        return False
    try:
        resp = _table.update_item(
            Key={'email': email.lower()},
            UpdateExpression="SET cv_pdf_key = :cv, cv_keywords_key = :kw, cv_updated_at = :ts",
            ExpressionAttributeValues={
                ':cv': cv_key,
                ':kw': kw_key,
                ':ts': int(__import__('time').time())
            },
            ConditionExpression="attribute_exists(email)",   # prevent creating a new item by mistake
            ReturnValues="NONE"
        )
        return True
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return False
        raise


def process(bucket_name: str, object_key: str):
    s3 = boto3.client("s3")

    object_key = unquote_plus(object_key)
    log.info(f"Processing s3://{bucket_name}/{object_key}")

    text = parse_cv_from_s3(s3, bucket_name, object_key)
    keywords = extract_keywords(text)

    parts = object_key.split("/")
    base = Path(parts[-1]).stem

    token = None
    email = None

    if len(parts) >= 3 and parts[0] == "cv_uploads":
        token = parts[1]
        keywords_key = f"cv_keywords/{token}/{base}_keywords.json"
    elif len(parts) >= 3 and parts[0] == "uploads":
        email = parts[1].lower()
        keywords_key = f"cv_keywords/{email}/{base}_keywords.json"
    else:
        keywords_key = f"cv_keywords/{base}_keywords.json"

    upload_keywords_to_s3(s3, bucket_name, keywords_key, keywords)
    log.info(f"Wrote keywords to s3://{bucket_name}/{keywords_key}")

    if USERS_TABLE:
        if token:
            ok = _update_user_with_cv_keys(token, object_key, keywords_key)
            log.info(f"DDB update by token={token}: {'ok' if ok else 'not found'}")
        elif email:
            ok = set_cv_keys_by_email(email, object_key, keywords_key)
            log.info(f"DDB update by email={email}: {'ok' if ok else 'not found'}")

    return {"bucket": bucket_name, "keywords_key": keywords_key, "token": token, "email": email}