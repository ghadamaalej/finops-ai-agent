from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    debug: bool = True
    default_scope: str = "subscription"

    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str
    LANGCHAIN_TRACING_V2: bool = True

    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-5.6-luna"
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
    AZURE_OPENAI_TIMEOUT_SECONDS: float = 250.0

    DATABASE_URL: str = (
        "postgresql://postgres:admin@localhost:5432/finops_agent"
    )

    AZURE_TENANT_ID: str
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_SUBSCRIPTION_ID: str

    FRONTEND_ORIGIN: str = "http://localhost:5173"
    ENTRA_REDIRECT_URI: str = "http://localhost:5173/signin"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()