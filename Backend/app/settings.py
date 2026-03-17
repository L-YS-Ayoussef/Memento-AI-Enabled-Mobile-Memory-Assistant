from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    # API keys
    GOOGLE_API_KEY: str

    # Long memory DB
    WEAVIATE_URL: str
    WEAVIATE_API_KEY: str

    # Short-term memory DB
    STATE_DB_URL: str

    BUSINESS_DB_URL: str
    
    # Scheduler
    # SCHEDULER_URL: str

    # llms
    CHAT_MODEL: str

    # Graph state
    MESSAGE_SUMMARY_TRIGGER: int = 20
    MAX_KEPT_MESSAGES: int = 5          # the number of messages to keep in the conversation history 


    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_TIME: int = 42  # in weeks

    # Observability
    # LANGSMITH_TRACING: bool
    # LANGSMITH_ENDPOINT: str
    # LANGSMITH_API_KEY: str
    # LANGSMITH_PROJECT: str

settings = Settings()