# user_management/api_cv.py  (new file or add to your /auth router module)
import os
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import boto3
from .auth import get_current_user  # your existing auth dependency that yields UserInDB

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
def presign(p: PresignIn, user = Depends(get_current_user)):
    try:
        s3, bucket = _s3_bucket()
        token = getattr(user, "verify_token", None) or getattr(user, "token", None) \
                or (user.get("verify_token") if isinstance(user, dict) else None) \
                or (user.get("token") if isinstance(user, dict) else None)
        if not token:
            raise RuntimeError("user token missing on principal")

        key = f"uploads/{token}/{p.filename}"
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