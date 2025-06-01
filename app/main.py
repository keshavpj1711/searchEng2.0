# Starting up FASTAPI app instance
from fastapi import FastAPI

# importing the pydantic models to be used
from app.models.article import Article, ArticleCreate;
from datetime import datetime;


# Creating FASTAPI app instance 
app = FastAPI(
  # Defining metadata for our api
  title="Scalable Search Engine API",
  description="API for searching and indexing data in db",
  version="0.1.0"  # To keep track of updates
)


# Defining endpoints

# / : root endpoint, this will be a greeting 
@app.get(
  "/", 
  tags=["Root"])
async def greet_user():
  return {
    "message": "Welcome!"
  }

# /status 
@app.get(  # A decorator to tell immediately following fn to process HTTP GET request
  "/status", 
  summary="Get API Status",
  tags=["General"]
)
async def get_status():
  # Return status of the api 
  return {
    "status": "API is up and running",
    "message": "Operational"
  }

# /documents: will be used add document to our db. It'll be a POST request
# The data for the new document (title, URL, and content) will be sent in the request body as JSON.
@app.post(
  "/documents",
  response_model=Article,  # Defines the model for response of the post request
  status_code=201,
  summary="Add a new document", 
  tags=["Documents"]
)
async def add_document(article_data: ArticleCreate):
  print(f"Received document to add: '{article_data.title}' at URL: {article_data.url}")

  # For testing purpose i am adding some mock data here
  mock_id = 1 # In reality, this would come from the database sequence
  mock_retrieved_at = datetime.now()

  return Article(
    id=mock_id,
    title=article_data.title,
    url=article_data.url,
    content=article_data.content,
    retrieved_at=mock_retrieved_at
  )

@app.get(
  "/search", 
  summary="Search for documents",
  tags=["Search"],
)
async def search_documents(query: str):
  print(f"Recieved search query: '{query}'")

  # Later on we will process this query 
  # Use the TF-IDF scores to search for matching documents
  # Rank the results
  # Return the list of documents

  mock_results = [
    {"id": 101, "title": "Mock Result 1 for " + query, "relevance_score": 0.95, "url": "http://example.com/result1"},
    {"id": 102, "title": "Another Mock Result for " + query, "relevance_score": 0.87, "url": "http://example.com/result2"}
  ]

  return {
    "query recieved": query,
    "search results": mock_results,
  }
