from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  
    )

    AWS_REGION: str | None = Field(None, env="AWS_REGION")
    AWS_ACCESS_KEY_ID: str | None = Field(None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = Field(None, env="AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN: str | None = Field(None, env="AWS_SESSION_TOKEN")
    AWS_ENDPOINT_URL: str | None = Field(None, env="AWS_ENDPOINT_URL")
    FROM_EMAIL: str | None = Field(None, env="FROM_EMAIL")
    SENDGRID_API_KEY: str | None = Field(None, env="SENDGRID_API_KEY")
    NOTIFICATIONS_PROVIDER: str = Field("console", env="NOTIFICATIONS_PROVIDER")

settings = Settings()
