from fastapi import FastAPI
from starlette.types import Message;

# Creating FASTAPI app instance 
app = FastAPI(
  # Defining metadata for our api
  title="Scalable Search Engine API",
  description="API for searching and indexing data in db",
  version="0.1.0"  # To keep track of updates
)


# Defining endpoints

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