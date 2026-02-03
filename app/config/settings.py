import os
import uuid

from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = ".env" + (
    ("." + os.getenv("ENV_MODE", "")) if os.getenv("ENV_MODE", False) else ""
)


class Settings(BaseSettings):
    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str
    PROJECT_VERSION: str
    SERVICE_AK_HEADER: str
    SERVICE_API_KEY: str
    NEO4J_HOSTNAME: str
    NEO4J_AUTH: str
    NEO4J_DATABASE: str

    model_config = SettingsConfigDict(env_file=env_file, extra="ignore")


settings = Settings()
