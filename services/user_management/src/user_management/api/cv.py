# user_management/api_cv.py  (new file or add to your /auth router module)
import os
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import boto3
from user_management.main import CurrentUser, get_current_user

router = APIRouter(prefix="/me/cv", tags=["me"])

class PresignIn(BaseModel):
    filename: str
    content_type: str = "application/pdf"
    max_size: int = 5 * 1024 * 1024

class PresignOut(BaseModel):
    key: str
    url: str
    fields: dict

def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"missing env var {name}")
    return v

@lru_cache(maxsize=1)
def _s3_bucket():
    s3 = boto3.resource("s3")
    bucket = _require("CV_S3_BUCKET")
    return s3, bucket


@router.post("/presign", response_model=PresignOut)
@router.post("/presign/", response_model=PresignOut)
@router.post("/presign", response_model=PresignOut)
def presign(p: PresignIn, current_user: CurrentUser = Depends(get_current_user)):
    """
    Returns a presigned POST for direct S3 upload. Namespaces by a stable user identifier.
    """
    try:
        s3, bucket = _s3_bucket()

        def _get(u, name):
            return getattr(u, name, None) if hasattr(u, name) else u.get(name)

        user_ns = _get(current_user, "id") or _get(current_user, "user_id") \
                  or _get(current_user, "token") or _get(current_user, "verify_token") \
                  or _get(current_user, "email")

        if not user_ns:
            raise RuntimeError("no stable user identifier on current_user")

        key = f"uploads/{user_ns}/{p.filename}"
        fields = {"Content-Type": p.content_type}
        conditions = [
            {"Content-Type": p.content_type},
            ["content-length-range", 1, p.max_size],
            {"bucket": bucket},
        ]

        presigned = s3.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=300,
        )
        return {"key": key, "url": presigned["url"], "fields": presigned["fields"]}

    except Exception as e:
        print(f"[presign] {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail="presign_failed")
@router.get("/ping")
def ping():
    return {"ok": True}