from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Debug
    debug: bool = True
    default_scope: str = "subscription"
    
    # LangChain
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str
    LANGCHAIN_TRACING_V2: bool = True
    
    # Ollama
    OLLAMA_MODEL: str
    OLLAMA_BASE_URL: str
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:admin@localhost:5432/finops_agent"
    
    # Azure Authentication - AJOUTEZ CES LIGNES
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
        extra="ignore" 
    )

settings = Settings()
