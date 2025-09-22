from __future__ import annotations
import os
import re
from uuid import uuid4
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

router = APIRouter(prefix="/cv", tags=["cv"])
auth = HTTPBearer()

AWS_REGION         = os.getenv("AWS_REGION")
CV_BUCKET          = os.environ["CV_BUCKET"]
USERS_TABLE_NAME   = os.environ["USERS_TABLE_NAME"]
PARTITION_KEY_NAME = os.getenv("USERS_TABLE_PK", "pk")

EMAIL_GSI_NAME     = os.getenv("USERS_EMAIL_GSI", "")
EMAIL_ATTR_NAME    = os.getenv("USERS_EMAIL_ATTR", "email")
USER_ID_GSI_NAME   = os.getenv("USERS_USERID_GSI", "")
USER_ID_ATTR_NAME  = os.getenv("USERS_USERID_ATTR", "user_id")

JWT_KEY            = os.environ["JWT_SECRET_KEY"]
ALGS               = ["HS256"]

dynamodb = boto3.resource("dynamodb")
s3r      = boto3.resource("s3")

users_tbl = dynamodb.Table(USERS_TABLE_NAME)
s3c = s3r.meta.client

def current_user(creds: HTTPAuthorizationCredentials = Depends(auth)):
    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_KEY, algorithms=ALGS)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

_EMAIL_RE = re.compile(r".+@.+\..+")

def _looks_like_email(value: str) -> bool:
    return bool(_EMAIL_RE.fullmatch(value))

def get_user_by_sub(sub: str) -> Optional[Dict[str, Any]]:
    try:
        resp = users_tbl.get_item(Key={PARTITION_KEY_NAME: sub})
        item = resp.get("Item")
        if item:
            return item
    except ClientError as e:
        print(f"[get_user_by_sub] GetItem error: {e}")

    if EMAIL_GSI_NAME and _looks_like_email(sub):
        try:
            q = users_tbl.query(
                IndexName=EMAIL_GSI_NAME,
                KeyConditionExpression=Key(EMAIL_ATTR_NAME).eq(sub),
                Limit=1,
            )
            items = q.get("Items") or []
            if items:
                return items[0]
        except ClientError as e:
            print(f"[get_user_by_sub] Query email GSI error: {e}")

    if USER_ID_GSI_NAME:
        try:
            q = users_tbl.query(
                IndexName=USER_ID_GSI_NAME,
                KeyConditionExpression=Key(USER_ID_ATTR_NAME).eq(sub),
                Limit=1,
            )
            items = q.get("Items") or []
            if items:
                return items[0]
        except ClientError as e:
            print(f"[get_user_by_sub] Query user_id GSI error: {e}")

    return None

class PresignIn(BaseModel):
    filename: str
    content_type: str = "application/pdf"

@router.post("/presign")
def presign_upload(p: PresignIn, user=Depends(current_user)):
    sub = user["sub"]
    u = get_user_by_sub(sub)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if not u.get("is_verified"):
        raise HTTPException(status_code=403, detail="User not verified")

    key = f"cv_uploads/{sub}/{uuid4()}_{p.filename}"

    try:
        url = s3c.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": CV_BUCKET,
                "Key": key,
                "ContentType": p.content_type,
                "Metadata": {"user-sub": sub},
            },
            ExpiresIn=900,
        )
    except ClientError as e:
        print(f"[presign_upload] presign error: {e}")
        raise HTTPException(status_code=500, detail="Failed to presign upload URL")

    return {"upload_url": url, "bucket": CV_BUCKET, "key": key}

@router.get("")
def get_my_cv(user=Depends(current_user)):
    sub = user["sub"]
    u = get_user_by_sub(sub)
    if not u or not u.get("is_verified"):
        raise HTTPException(status_code=403, detail="Invalid or unverified user")

    # Return just the keys; you can presign GETs on a separate endpoint if you want
    return {
        "cv_pdf_key": u.get("cv_pdf_key"),
        "cv_keywords_key": u.get("cv_keywords_key"),
        "updated_at": u.get("updated_at"),
    }

@router.get("/ping")
def ping(): return {"ok": True}
