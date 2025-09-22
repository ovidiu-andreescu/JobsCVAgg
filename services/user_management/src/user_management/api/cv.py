from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import boto3, os
from ..db.dynamodb import get_user_by_token

router = APIRouter(prefix="/users", tags=["cv"])
s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "eu-central-1"))
BUCKET = os.getenv("CV_S3_BUCKET")

class PresignIn(BaseModel):
    filename: str
    content_type: str = "application/pdf"

@router.post("/{token}/cv/presign")
def presign_upload(token: str, p: PresignIn):
    u = get_user_by_token(token)

    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if not u.get("is_verified"):
        raise HTTPException(status_code=403, detail="User not verified")

    key = f"cv_uploads/{token}/{uuid4()}_{p.filename}"
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": BUCKET,
            "Key": key,
            "ContentType": p.content_type,
            "Metadata": {"user-token": token}
        },
        ExpiresIn=900
    )

    return {"upload_url": url, "bucket": BUCKET, "key": key}

@router.get("/{token}/cv")
def get_my_cv(token: str):
    u = get_user_by_token(token)
    if not u or not u.get("is_verified"):
        raise HTTPException(status_code=403, detail="Invalid or unverified token")
    return {
        "cv_pdf_key": u.get("cv_pdf_key"),
        "cv_keywords_key": u.get("cv_keywords_key"),
    }