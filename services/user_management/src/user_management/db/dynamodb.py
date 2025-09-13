import os
import boto3
from dotenv import load_dotenv

load_dotenv()

aws_region = os.getenv("AWS_REGION", "eu-west-1")
table_name = os.getenv("DDB_TABLE_USERS", "users")

session = boto3.session.Session(
    aws_access_key_id=os.getenv("AKIA5P2RGIRSTZGR7RWG"),
    aws_secret_access_key=os.getenv("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"),
    region_name=aws_region,
)


dynamodb = session.resource("dynamodb")
_table = dynamodb.Table(table_name)

def get_by_email(email: str):
    resp = _table.get_item(Key={"email": email.lower()})
    return resp.get("Item")

def add_user(user):
    _table.put_item(Item={"email": user.email, "password_hash": user.password_hash})
