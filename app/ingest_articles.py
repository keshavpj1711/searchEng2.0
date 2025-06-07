# This is a script to ingest or populate our database from featured_sample_articles.json 
# So ealier our ingest articles used to create a post request for every article that has to be added 
# But now it directly adds data to our db instead of adding it through our api 

import json
import sqlite3
from app.core.config import settings
from datetime import datetime, timezone
from pathlib import Path
from app.db.database_utils import get_db_connection


def main():
  """Main function to ingest articles directly into database"""
  JSON_FILE_PATH = settings.FETCHED_ARTICLES

  # Load articles from JSON file
  try:
    with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
      articles = json.load(f)
    print(f"Loaded {len(articles)} articles from {JSON_FILE_PATH}")
  except FileNotFoundError:
    print(f"Error: {JSON_FILE_PATH} not found. Make sure you run the crawler first.")
    return
  except json.JSONDecodeError:
    print(f"Error: Invalid JSON in {JSON_FILE_PATH}. Please check the file.")
    return

  # Prepare data for bulk insertion
  articles_data = []
  for article in articles:
    if article.get('content'):  # Only insert articles with content
      # Ensure retrieved_at is in proper format
      retrieved_at = article.get('retrieved_at')
      if not retrieved_at:
        retrieved_at = datetime.now(timezone.utc).isoformat()
      
      articles_data.append((
        article['title'],
        article['url'], 
        article['content'],
        retrieved_at
      ))

  if not articles_data:
    print("No valid articles found to insert.")
    return

  # Bulk insert into database
  try:
    with get_db_connection() as conn:
      cursor = conn.cursor()
      
      # Use executemany for efficient bulk insertion
      insert_sql = """
        INSERT OR IGNORE INTO articles (title, url, content, retrieved_at) 
        VALUES (?, ?, ?, ?)
      """
      
      cursor.executemany(insert_sql, articles_data)
      conn.commit()
      
      # Get count of inserted rows
      inserted_count = cursor.rowcount
      print(f"Successfully inserted {len(articles_data)} articles into database")
      
      # Verify total count in database
      cursor.execute("SELECT COUNT(*) FROM articles")
      total_count = cursor.fetchone()[0]
      print(f"Database now contains {total_count} total articles")
      
  except sqlite3.IntegrityError as e:
    print(f"Database integrity error: {e}")
    print("Some articles may have duplicate URLs (this is normal)")
  except sqlite3.Error as e:
    print(f"Database error during bulk insertion: {e}")
    raise
  except Exception as e:
    print(f"Unexpected error during article ingestion: {e}")
    raise

  print("Finished ingesting all articles directly into database.")

if __name__ == "__main__":
  main()