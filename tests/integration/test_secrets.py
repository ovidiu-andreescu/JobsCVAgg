from agg_common.secrets_loader import clear_secret_cache, get_secret
import pytest, os, boto3, uuid

@pytest.mark.integration
def test_localstack():
    clear_secret_cache()
    endpoint = os.getenv("SECRETS_ENDPOINT_URL") or os.getenv("LOCALSTACK_URL","http://localstack:4566")
    region = os.getenv("AWS_DEFAULT_REGION", "eu_central_1")
    client = boto3.client("secretsmanager", endpoint_url=endpoint, region_name=region,
                          aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
                          aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"))
    name = f"it-{uuid.uuid4().hex[:8]}"
    client.create_secret(Name=name, SecretString="hello")

    try:
        assert get_secret(name) == "hello"
    finally:
        client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)