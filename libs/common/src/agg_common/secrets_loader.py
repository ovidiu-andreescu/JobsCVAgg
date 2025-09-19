# libs/src/common/secrets_loader.py
import json
import os
from functools import lru_cache
import base64

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
except Exception:
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception
    EndpointConnectionError = Exception
    class Config:
        def __init__(self, *a, **k): ...

def _runtime_prefix(prefix: str | None) -> str:
    return (prefix if prefix is not None else os.getenv("SECRETS_PREFIX", "")).strip("/")

def _qualify(name: str, prefix: str | None) -> str:
    p = _runtime_prefix(prefix)
    return f"{p}/{name}" if p else name

def _env_key(qualified: str) -> str:
    return qualified.replace("/", "_").upper()

def _client():
    if boto3 is None:
        return None
    region = os.getenv("AWS_DEFAULT_REGION", "eu-central-1")
    endpoint = os.getenv("SECRETS_ENDPOINT_URL") or os.getenv("LOCALSTACK_URL")
    session = boto3.session.Session(region_name=region)
    return session.client(
        "secretsmanager",
        endpoint_url=endpoint,
        config=Config(retries={"max_attempts": 5, "mode": "standard"}),
    )

def clear_secret_cache() -> None:
    get_secret.cache_clear()

@lru_cache(maxsize=256)
def get_secret(
    name: str,
    *,
    prefix: str | None = None,
    default: str | None = None,
) -> str:
    qualified = _qualify(name, prefix)

    env_val = os.getenv(_env_key(qualified))
    if env_val is not None:
        return env_val

    if os.getenv("SECRETS_OFFLINE", "").lower() == "true":
        if default is not None:
            return default
        raise RuntimeError(f"Secret '{qualified}' missing (offline); set {_env_key(qualified)} or pass default.")

    client = _client()
    if client is not None:
        try:
            resp = client.get_secret_value(SecretId=qualified)
            if resp.get("SecretString") is not None:
                return resp["SecretString"]
            return base64.b64decode(resp["SecretBinary"]).decode("utf-8")
        except (NoCredentialsError, EndpointConnectionError):
            pass
        except ClientError as e:
            if default is not None and e.response.get("Error", {}).get("Code") in {
                "ResourceNotFoundException",
                "AccessDeniedException",
                "DecryptionFailure",
            }:
                return default
            raise

    if default is not None:
        return default
    raise RuntimeError(f"Missing secret '{qualified}'. Set env {_env_key(qualified)} or configure Secrets Manager.")

def get_json_secret(
    name: str,
    *,
    prefix: str | None = None,
    default: dict | list | None = None,
):
    raw_default = None if default is None else json.dumps(default)
    raw = get_secret(name, prefix=prefix, default=raw_default)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Secret '{_qualify(name, prefix)}' is not valid JSON") from e
