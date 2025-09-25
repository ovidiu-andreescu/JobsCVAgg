# user_management/api/cv.py
import os, boto3
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from user_management.auth_deps import CurrentUser, get_current_user

router = APIRouter(prefix="/me/cv", tags=["me"])

@router.get("/ping")
def ping(): return {"ok": True}

class PresignIn(BaseModel):
    filename: str
    content_type: str = "application/pdf"
    max_size: int = 5 * 1024 * 1024

class PresignOut(BaseModel):
    key: str
    url: str
    fields: dict

class CvStatus(BaseModel):
    cv_pdf_key: str | None = None
    cv_keywords_key: str | None = None
    keywords: list[str] | None = None

def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"missing env var {name}")
    return v

def _latest_user_pdf_key(s3, bucket: str, email: str) -> str | None:
    prefix = f"uploads/{email}/"
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    contents = resp.get("Contents", [])
    pdf_objs = [c for c in contents if c["Key"].lower().endswith(".pdf")]
    if not pdf_objs:
        return None
    pdf_objs.sort(key=lambda x: x["LastModified"], reverse=True)
    return pdf_objs[0]["Key"]


@lru_cache(maxsize=1)
def _s3_and_bucket():
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "eu-central-1"))
    return s3, _require("CV_S3_BUCKET")

@router.post("/presign", response_model=PresignOut)
@router.post("/presign/", response_model=PresignOut)  # tolerate trailing slash
def presign(p: PresignIn, current_user: CurrentUser = Depends(get_current_user)):
    try:
        s3, bucket = _s3_and_bucket()
        key = f"uploads/{current_user.email}/{p.filename}"

        fields = {"Content-Type": p.content_type}
        conditions = [
            {"Content-Type": p.content_type},
            ["content-length-range", 1, p.max_size],
            {"bucket": bucket},
        ]
        presigned = s3.generate_presigned_post(
            Bucket=bucket, Key=key, Fields=fields, Conditions=conditions, ExpiresIn=300
        )
        return {"key": key, "url": presigned["url"], "fields": presigned["fields"]}
    except Exception as e:
        print(f"[presign] {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail="presign_failed")

@router.get("", response_model=CvStatus)
@router.get("/", response_model=CvStatus)
def get_cv_status(current_user: CurrentUser = Depends(get_current_user)):
    s3, bucket = _s3_and_bucket()
    pdf_key = _latest_user_pdf_key(s3, bucket, current_user.email)
    if not pdf_key:
        raise HTTPException(status_code=204, detail="no_cv")

    if pdf_key.lower().endswith(".pdf"):
        base = pdf_key[:-4]
    else:
        base = pdf_key
    kw_key = f"{base}.keywords.json"

    try:
        obj = s3.get_object(Bucket=bucket, Key=kw_key)
        body = obj["Body"].read()
        import json
        data = json.loads(body.decode("utf-8")) if body else {}
        kws = data.get("keywords")
        return CvStatus(cv_pdf_key=pdf_key, cv_keywords_key=kw_key, keywords=kws if isinstance(kws, list) else None)
    except s3.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="cv_not_ready")
    except Exception as e:
        print(f"[get_cv_status] {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail="cv_status_failed")