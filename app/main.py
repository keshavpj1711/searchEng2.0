# Starting up FASTAPI app instance
from contextlib import asynccontextmanager
from fastapi import FastAPI

# importing the pydantic models to be used
from app.models.article import Article, ArticleCreate
from datetime import datetime, timezone

# Setting up and connecting to db
from app.db.database_utils import init_db, get_db_connection

# Sending and recieving from db and managing responses
import sqlite3
from fastapi import HTTPException

# Building and getting TF-IDF scores 
from app.services.build_tfidf_data import build_tfidf_data, get_tfidf_data
from app.services.tfidf import calculate_tfidf, preprocess_text

# Building inv index 
from app.services.build_inv_index import build_inverted_index

# Performing Search
from app.services.search_logic import perform_search


# App startup defined 
@asynccontextmanager
async def lifespan(app: FastAPI):
  print("FastAPI application startup: Initializing database via lifespan...")
  init_db()
  print("Database initialization complete via lifespan.")

  # The order matters here since first we need to build our tfidf_data
  # Then only we can build the inverted index according to it

  # Build TF-IDF data structures
  print("Building TF-IDF data structures...")
  build_tfidf_data()
  print("TF-IDF data structures ready.")

  # Build inverted index
  print("Building inverted index...")
  build_inverted_index()
  print("Inverted index ready.")

  yield

  # Code to run on shutdown (if any)
  print("FastAPI application shutdown.")



# Creating FASTAPI app instance 
app = FastAPI(
  lifespan=lifespan,  # Passing the lifespan context manager 
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

  final_retrieved_at: datetime
  # Checking if the retrieved_at was provided by the client or not
  # This is just to remove variations in timezone so that all the retrieved_at are in UTC 
  if article_data.retrieved_at:
    if article_data.retrieved_at.tzinfo is None:
      # This case is less likely if your JSON always has TZ, but good for safety.
      print(f"Warning: Received naive datetime for retrieved_at: {article_data.retrieved_at}. Assuming UTC.")
      final_retrieved_at = article_data.retrieved_at.replace(tzinfo=timezone.utc)
    else:
      final_retrieved_at = article_data.retrieved_at
    print(f"Using provided retrieved_at: {final_retrieved_at.isoformat()}")
  else:
    # If not provided, generate it now as UTC.
    final_retrieved_at = datetime.now(timezone.utc)
    print(f"Generated new retrieved_at (UTC): {final_retrieved_at.isoformat()}")

  # Convert datetime object to ISO 8601 string for database storage
  retrieved_at_iso_string = final_retrieved_at.isoformat()
  
  # Convert HttpUrl to string for database storage
  url_string = str(article_data.url)

  # Calculate TF-IDF scores for this document
  tfidf_data = get_tfidf_data()
  if tfidf_data['idf_scores']:
    # Combine title and content, giving title extra weight
    combined_text = f"{article_data.title} {article_data.title} {article_data.content}"
    tokens = preprocess_text(combined_text)
    tfidf_scores = calculate_tfidf(tokens, tfidf_data['idf_scores'])
    print(f"Calculated TF-IDF scores for {len(tfidf_scores)} terms")
  else:
    print("No IDF data available yet")
    tfidf_scores = {}

  # TODO: Day 5 - Use Celery to update TF-IDF data and inverted index asynchronously
  # Currently new documents won't appear in search until server restart


  # Inserting article into db
  try:
    with get_db_connection() as conn:
      cursor = conn.cursor()
      sql = """
        INSERT INTO articles (title, url, content, retrieved_at) 
        VALUES (?, ?, ?, ?)
      """
      cursor.execute(sql, (
        article_data.title, 
        url_string, 
        article_data.content, 
        retrieved_at_iso_string 
      ))
      conn.commit()
      actual_id_from_db = cursor.lastrowid # Get the ID of the newly inserted row
      print(f"Article '{article_data.title}' inserted into DB with ID: {actual_id_from_db}")
  
  except sqlite3.IntegrityError as e:
    # commonly occurs if the URL (which is UNIQUE) already exists
    print(f"Database IntegrityError (e.g., URL already exists): {e}")
    raise HTTPException(
      status_code=409, # Conflict
      detail=f"Article with this URL already exists or other integrity constraint failed: {str(article_data.url)}"
    )
  except sqlite3.Error as e:
    print(f"Database error during article insertion: {e}")
    raise HTTPException(
      status_code=500, # Internal Server Error
      detail="An error occurred while inserting the article into the database."
    )
  except Exception as e:
    print(f"An unexpected error occurred during article insertion: {e}")
    raise HTTPException(
      status_code=500,
      detail="An unexpected error occurred."
    )

  # Construct the response using the Article Pydantic model
  return Article(
    id=actual_id_from_db,
    title=article_data.title,
    url=article_data.url, # Pydantic model will handle HttpUrl type
    content=article_data.content,
    retrieved_at=final_retrieved_at # Return the datetime object
  )

@app.get(
  "/search", 
  summary="Search for documents",
  tags=["Search"],
)
async def search_documents(query: str, limit: int = 10):
  """Search for documents using TF-IDF scoring and inverted index"""
  print(f"Received search query: '{query}'")

  # Later on we will process this query 
  # Use the TF-IDF scores to search for matching documents
  # Rank the results
  # Return the list of documents

  # All these above tasks are now being done by our search_logic.py
  
  # Call your search logic
  search_result = perform_search(query, limit)
  
  return search_result

