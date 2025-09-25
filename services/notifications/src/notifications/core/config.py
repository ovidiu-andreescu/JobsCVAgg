from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "Notifications"
    NOTIFICATIONS_PROVIDER: str = Field(default="console", description="console|sendgrid|ses")
    AWS_REGION: str = Field(default="eu-central-1")

    SENDGRID_API_KEY: str | None = None
    FROM_EMAIL: str | None = None

    SES_FROM_EMAIL: str | None = None

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")


settings = Settings()