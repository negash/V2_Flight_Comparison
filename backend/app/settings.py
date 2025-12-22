"""Application settings module."""
from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    OPENAI_API_KEY: str
    AMADEUS_API_KEY: str
    AMADEUS_API_SECRET: str

    class Config:
        """Configuration for loading environment variables."""
        env_file = ".env"


settings = Settings()
