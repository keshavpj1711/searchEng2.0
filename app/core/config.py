import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  FETCHED_ARTICLES: str = "./data/fetched_sample_articles.json"
  SQLITE_DB: str = "./data/wikipedia_articles.db"

  # Redis configuration
  REDIS_HOST: str = "localhost"
  REDIS_PORT: int = 6379
  REDIS_DB: int = 0

  class Config: 
    env_file = ".env"
    env_file_encoding = "utf-8"
    extra = "ignore"

settings = Settings()

# print(f"Database file configured at: {settings.SQLITE_DB}")