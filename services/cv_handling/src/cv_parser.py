import boto3
import io
from PyPDF2 import PdfReader
from botocore.exceptions import BotoCoreError, ClientError
from libs.common.src.agg_common import secrets_loader

def parse_cv_from_s3(bucket_name: str, object_name: str) -> str:
    """
    Arguments:
    - bucket_name: S3 bucket name
    - object_name: S3 object key (filename in the bucket)
    Returns:
    - Extracted text from the PDF CV
    Raises:
    - RuntimeError on failure (again, hope not)
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

    # Fetches the PDF from S3
    try:
        pdf_obj = s3_client.get_object(Bucket=bucket_name, Key=object_name)
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed fetching PDF from S3: {e}")

    # Reads the PDF content and extracts text
    file_stream = io.BytesIO(pdf_obj['Body'].read())
    pdf_reader = PdfReader(file_stream)
    text = []
    for page in pdf_reader.pages:
        try:
            text.append(page.extract_text() or "")
        except Exception:
            continue

    return "\n".join(text)