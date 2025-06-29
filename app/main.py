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
from app.services.build_tfidf_data import get_prebuilt_tfidf_data, get_tfidf_data
from app.services.tfidf import calculate_tfidf, preprocess_text

# Building inv index 
from app.services.build_inv_index import get_prebuilt_inv_index

# Performing Search
from app.services.search_logic import perform_search

# adding celery tasks to update search index or inverted index in background when a new document is added
from app.tasks.indexing_tasks import update_search_index

# for checking cache staleness
from app.db.database_utils import fetch_all_articles
from app.services.redis_client import get_redis_client

# for setting up for new user
from app.setup import is_first_time, starting_setup


# App startup defined 
@asynccontextmanager
async def lifespan(app: FastAPI):
  # Setting up for first time
  print("Output", is_first_time())

  if is_first_time():
    print("New Setup detected - fetching articles and setting up db")
    await starting_setup()
  else:
    print("Starting...")

  print("FastAPI application startup: Initializing database via lifespan...")
  init_db()
  print("Database initialization complete via lifespan.")

  # Checking for cache stalness
  should_refresh = await check_cache_freshness()
  print(should_refresh)
  if should_refresh:
    print("Cache appears stale - refreshing synchronously...")
    update_search_index() # Using it as a normal fn 
    print("Cache refresh completed.")

  # The order matters here since first we need to build our tfidf_data
  # Then only we can build the inverted index according to it

  # Build TF-IDF data structures
  print("Building TF-IDF data structures...")
  get_prebuilt_tfidf_data()

  print("TF-IDF data structures ready.")

  # Build inverted index
  print("Building inverted index...")
  get_prebuilt_inv_index()

  print("Inverted index ready.")

  yield

  # Code to run on shutdown (if any)
  print("FastAPI application shutdown.")


async def check_cache_freshness() -> bool:
  """Check if cache needs refresh based on document count mismatch"""
  try:    
    # Get actual document count from database
    db_articles = fetch_all_articles()
    db_count = len(db_articles)
    
    # Get cached document count
    client = get_redis_client()
    if client is None:
      return True  # No Redis, need to refresh
    
    cached_count_raw = client.get("tfidf:total_documents")
    cached_count = int(cached_count_raw) if cached_count_raw else 0
    
    # If counts don't match, cache is stale
    if db_count != cached_count:
      print(f"Cache mismatch: DB has {db_count} docs, cache has {cached_count}")
      return True
    
    return False
  except Exception as e:
    print(f"Error checking cache freshness: {e}")
    return True  # On error refresh just to be safe


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

      # Celery task to handle rebuilding the inv_index
      # Trigger background re-indexing (async)
      print("Triggering background index update via Celery...")
      update_search_index.delay()
      print("Background task queued successfully.")
      
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

