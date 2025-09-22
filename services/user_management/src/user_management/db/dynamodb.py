import os
import boto3
from typing import Optional, Dict, Any
from boto3.dynamodb.conditions import Attr, Key
from user_management.schemas.auth import UserInDB

dynamodb = boto3.resource("dynamodb")

USERS_TABLE_NAME = os.environ.get("USERS_TABLE_NAME")
if not USERS_TABLE_NAME:
    raise ValueError("Missing required environment variable: USERS_TABLE_NAME")

_table = dynamodb.Table(USERS_TABLE_NAME)


def create_user(user: UserInDB):
    try:
        item = user.model_dump()

        _table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(email)'
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        raise ValueError("Email already registered")

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    response = _table.get_item(Key={'email': email.lower()})
    return response.get("Item")


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    # requires GSI: verify_token-index
    resp = _table.query(
        IndexName="verify_token-index",
        KeyConditionExpression=Key("verify_token").eq(token),
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None


def mark_verified(email: str):
    _table.update_item(
        Key={'email': email.lower()},
        UpdateExpression="SET is_verified = :v",
        ExpressionAttributeValues={':v': True},
    )


def set_cv_keys_by_token(token: str, cv_key: str, kw_key: str) -> bool:
    u = get_user_by_token(token)
    if not u:
        return False
    email = u["email"].lower()
    _table.update_item(
        Key={'email': email},
        UpdateExpression="SET cv_pdf_key = :cv, cv_keywords_key = :kw",
        ExpressionAttributeValues={':cv': cv_key, ':kw': kw_key},
    )
    return True