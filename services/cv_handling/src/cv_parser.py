import boto3
import io
from PyPDF2 import PdfReader
from botocore.exceptions import BotoCoreError, ClientError

def parse_cv_from_s3(s3_client, bucket_name: str, object_name: str) -> str:
    """
    Arguments:
    - s3_client: Boto3 S3 client
    - bucket_name: S3 bucket name
    - object_name: S3 object key (filename in the bucket)
    Returns:
    - Extracted text from the PDF CV
    Raises:
    - RuntimeError on failure (again, hope not)
    """
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