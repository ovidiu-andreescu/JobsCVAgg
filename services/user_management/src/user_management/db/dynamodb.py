import os
import boto3
from typing import Optional, Dict, Any

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
    from boto3.dynamodb.conditions import Attr

    response = _table.scan(
        FilterExpression=Attr('verify_token').eq(token)
    )
    items = response.get('Items', [])
    return items[0] if items else None


def mark_verified(email: str):
    _table.update_item(
        Key={'email': email.lower()},
        UpdateExpression="SET is_verified = :verified REMOVE verify_token",
        ExpressionAttributeValues={
            ':verified': True
        }
    )