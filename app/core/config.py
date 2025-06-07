import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  FETCHED_ARTICLES: str = "./data/fetched_sample_articles.json"
  SQLITE_DB: str = "./data/wikipedia_articles.db"

  # Redis configuration with Docker-friendly defaults
  REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
  REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6380')) 
  REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))

  class Config: 
    env_file = ".env"
    env_file_encoding = "utf-8"
    extra = "ignore"

settings = Settings()

# print(f"Database file configured at: {settings.SQLITE_DB}")