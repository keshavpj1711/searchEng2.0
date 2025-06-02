import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  FETCHED_ARTICLES: str = "./data/fetched_sample_articles.json"
  SQLITE_DB: str = "./data/wikipedia_articles.db"

  class Config: 
    env_file = ".env"
    env_file_encoding = "utf-8"
    extra = "ignore"

settings = Settings()

# print(f"Database file configured at: {settings.SQLITE_DB}")