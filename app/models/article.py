# FastAPI uses Pydantic models to define the expected structure of the request body and to validate the incoming data.
# Defining these models is important as when we will be add articles to it then also it'll will play an imp role

from pydantic import BaseModel, HttpUrl;
from typing import Optional;
from datetime import datetime;

class ArticleBase(BaseModel): 
  title: str
  url: HttpUrl # Pydantic will validate if this is a valid URL
  content: Optional[str] = None

class ArticleCreate(ArticleBase):
    # This model defines the data expected when creating a new article.
    # In our case it's same as ArticleBase
    pass

class Article(ArticleBase):
    # This model will represent an article as returned by the API,
    id: int
    # DB generated feilds like title url and content
    retrieved_at: datetime # Example of a field that might be added by the server

    class Config:
        from_attributes = True # Helps Pydantic convert ORM models to Pydantic models