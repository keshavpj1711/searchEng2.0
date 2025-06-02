# This is a script to ingest or populate our database from featured_sample_articles.json 
import json
import requests
from app.core.config import settings

API_ENDPOINT = "http://127.0.0.1:8000/documents" # We will be running this after turning our server on
JSON_FILE_PATH = settings.FETCHED_ARTICLES

# Lets load in the articles now
try:
  with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
    articles = json.load(f)
  print(f"Loaded {len(articles)} articles from {JSON_FILE_PATH}")
except FileNotFoundError:
  print(f"Error: {JSON_FILE_PATH} not found. Make sure you run the crawler first.")
  exit()
except json.JSONDecodeError:
  print(f"Error: Invalid JSON in {JSON_FILE_PATH}. Please check the file.")
  exit()

# Making post request for each article 
for article in articles:
  try:
    # Send a POST request to your API for every article, with all the relevent data 
    response = requests.post(API_ENDPOINT, json=article)
    response.raise_for_status() # Raise HTTP Error for bad responses 

    # Success message
    print(f"Article '{article['title']}' added successfully. Status Code: {response.status_code}")
  
  except requests.exceptions.RequestException as e:
    # Error 
    print(f"Error adding article '{article['title']}': {e}")
  except Exception as e:
    print(f"An unexpected error occurred while processing '{article['title']}': {e}")

print("Finished attempting to ingest all articles.")

