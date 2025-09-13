from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Auth
    SECRET_KEY: str = Field("change-me-in-env")
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRES_MIN: int = 60

    # AWS (optional)
    AWS_REGION: str | None = Field(None, env="AWS_REGION")
    DDB_TABLE_USERS: str | None = Field(None, env="DDB_TABLE_USERS")
    AWS_ENDPOINT_URL: str | None = Field(None, env="AWS_ENDPOINT_URL")
    AWS_ACCESS_KEY_ID: str | None = Field(None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = Field(None, env="AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN: str | None = Field(None, env="AWS_SESSION_TOKEN")

    # Notifications
    NOTIFICATIONS_BASE_URL: str = Field("http://127.0.0.1:5001", env="NOTIFICATIONS_BASE_URL")
    NOTIFICATIONS_CHANNEL: str = Field("console", env="NOTIFICATIONS_CHANNEL")
    PUBLIC_BASE_URL: str = Field("http://127.0.0.1:5000", env="PUBLIC_BASE_URL")

settings = Settings()
