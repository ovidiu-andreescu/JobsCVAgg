import os
from agg_common.secrets_loader import get_secret

_SECRETS_PREFIX = os.getenv('SECRETS_PREFIX')

def adzuna_app_id() -> str | None:
    return get_secret("adzuna_app_id", prefix=_SECRETS_PREFIX, default="")

def adzuna_app_key() -> str | None:
    return get_secret('adzuna_app_key', prefix=_SECRETS_PREFIX, default="")