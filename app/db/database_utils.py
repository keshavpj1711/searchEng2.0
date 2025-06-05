# Contains functions to connect to our SQLite db and create the articles table

import sqlite3
import os
from app.core.config import settings  # The settings instance that we created
from typing import List, Dict, Any

def get_db_connection():
  
  # Ensuring the dir before attempting to connect
  db_dir = os.path.dirname(settings.SQLITE_DB)
  if db_dir:  # Check if db_dir is not empty 
    os.makedirs(db_dir, exist_ok=True)
  conn = sqlite3.connect(settings.SQLITE_DB)
  conn.row_factory = sqlite3.Row # Allows accessing columns by name (e.g., row['title'])
  return conn


def create_articles_table():
  try:
    with get_db_connection() as conn: # 'with' statement ensures connection is closed
      cursor = conn.cursor()
      cursor.execute("""
          CREATE TABLE IF NOT EXISTS articles (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              url TEXT UNIQUE NOT NULL,
              content TEXT,
              retrieved_at TEXT NOT NULL
          );
      """)
      conn.commit() # Commit the changes (table creation)
      print("Table 'articles' checked/created successfully.")

  except sqlite3.Error as e:
    print(f"SQLite error when creating 'articles' table: {e}")
  except Exception as e:
    print(f"An unexpected error occurred during table creation: {e}")


def init_db():
  """
  Initializes the database. Currently, this just means creating the tables.
  """
  # Use the updated setting name: settings.SQLITE_DB
  print(f"Attempting to initialize database at: {settings.SQLITE_DB}")
  create_articles_table()
  print("Database initialization process complete.")


def fetch_all_articles() -> List[Dict[str, Any]]:
  """Fetch all articles with id, title, and content from database"""
  articles = []
  try:
    with get_db_connection() as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT id, title, content FROM articles WHERE content IS NOT NULL")
      rows = cursor.fetchall()
      for row in rows:
        articles.append({
          'id': row['id'],
          'title': row['title'],
          'content': row['content']
        })
  except Exception as e:
    print(f"Error fetching articles: {e}")
  return articles


def fetch_documents_by_ids(doc_ids: List[int]) -> List[Dict[str, Any]]:
  """Fetch specific documents by their IDs"""
  if not doc_ids:
    return []
  
  placeholders = ','.join(['?' for _ in doc_ids])
  articles = []
  try:
    with get_db_connection() as conn:
      cursor = conn.cursor()
      cursor.execute(f"SELECT id, title, url, content FROM articles WHERE id IN ({placeholders})", doc_ids)
      rows = cursor.fetchall()
      for row in rows:
        articles.append({
          'id': row['id'],
          'title': row['title'],
          'url': row['url'],
          'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content']
        })
  except Exception as e:
    print(f"Error fetching documents by IDs: {e}")
  return articles
