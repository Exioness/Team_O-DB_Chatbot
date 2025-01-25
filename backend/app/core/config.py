from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Database Query API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for database queries using LLM"
    
    # Database
    DB_HOST: str = "localhost"
    DB_NAME: str = "dvdrental"  # Main database for chat2sql
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    
    # Auth database
    AUTH_DB_HOST: str = "localhost"
    AUTH_DB_NAME: str = "chat_auth_db"
    AUTH_DB_USER: str = "postgres"  # Make sure this matches your PostgreSQL user
    AUTH_DB_PASSWORD: str = "postgres"  # Make sure this matches your PostgreSQL password
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key"  # Change this in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    OPENAI_API_KEY: str
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()
