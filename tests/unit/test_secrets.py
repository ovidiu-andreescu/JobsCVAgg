from agg_common.secrets_loader import clear_secret_cache, get_secret


def test_env_override(monkeypatch):
    clear_secret_cache()
    monkeypatch.setenv("SECRETS_PREFIX", "dev")
    monkeypatch.setenv("DEV_MY_KEY", "val")
    assert get_secret("my_key") == "val"
