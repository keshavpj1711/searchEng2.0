# This is to create a setup for a new user who wants to use this 

import os
import subprocess
import sys
from pathlib import Path
from app.db.database_utils import init_db
from app.core.config import settings
from app.crawler.crawler import run_crawler_operations_async
from app.ingest_articles import main as ingest_main

def is_first_time() -> bool:
  """Check if this is the first time setup"""
  setup_marker = Path(".search_engine_initialized")
  return not setup_marker.exists()


async def starting_setup():
  """Complete first-time setup: database, crawler, ingestion"""
  try:
    print("Starting Setup...")

    print("Setting up database...")
    setup_database()

    print("Running crawler to fetch articles...")
    await run_crawler()

    print("Initializing database tables...")
    init_db()

    print("Populating database with fetched articles...")
    ingest_articles()

    print("Marking setup as complete...")
    mark_as_initialized()

    print("Setup Completed!!")
  
  except Exception as e:
    print(f"Setup failed: {e}")
    cleanup_partial_setup()
    raise


def setup_database():
  """Create the database file if it doesn't exist"""
  db_path = Path(settings.SQLITE_DB)
  
  # Create data directory if it doesn't exist
  db_path.parent.mkdir(parents=True, exist_ok=True)
  
  # Create empty database file if it doesn't exist
  if not db_path.exists():
    db_path.touch()
    print(f"Created database file: {db_path}")
  else:
    print(f"Database file already exists: {db_path}")


async def run_crawler():
  """Run the crawler script to fetch articles"""
  try:
    print("Running crawler to fetch articles...")
    
    # Call the crawler functions to run it
    await run_crawler_operations_async()
    
    print("Crawler completed successfully")
    
    # Verify the files were created
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    featured_file = data_dir / "featured_articles_list.json"
    fetched_file = data_dir / "fetched_sample_articles.json"
    
    if not featured_file.exists():
      raise FileNotFoundError(f"Crawler didn't create: {featured_file}")
    if not fetched_file.exists():
      raise FileNotFoundError(f"Crawler didn't create: {fetched_file}")
      
    print(f"✅ Created: {featured_file}")
    print(f"✅ Created: {fetched_file}")
    
  except Exception as e:
    print(f"Error running crawler: {e}")
    raise


def ingest_articles():
  """Run the ingest articles script"""
  try:
    ingest_main()  # Now does direct bulk insertion
    print("Article ingestion completed successfully")
  except Exception as e:
    print(f"Error ingesting articles: {e}")
    raise


def mark_as_initialized():
  """Mark setup as complete"""
  from datetime import datetime
  
  setup_marker = Path(".search_engine_initialized")
  setup_info = {
    "initialized": True,
    "setup_date": datetime.now().isoformat(),
    "version": "1.0"
  }

  setup_marker.write_text(f"Setup completed on: {setup_info['setup_date']}")
  print(f"Marked as initialized: {setup_marker}")


def cleanup_partial_setup():
  """Clean up if setup fails partway through"""
  try:
    print("Cleaning up partial setup...")
    
    # Remove database file
    db_path = Path(settings.SQLITE_DB)
    if db_path.exists():
      db_path.unlink()
      print(f"Removed: {db_path}")
    
    # Remove JSON files
    data_dir = Path("data")
    for json_file in ["featured_articles_list.json", "fetched_sample_articles.json"]:
      file_path = data_dir / json_file
      if file_path.exists():
        file_path.unlink()
        print(f"Removed: {file_path}")
    
    # Remove initialization marker
    marker = Path(".search_engine_initialized")
    if marker.exists():
      marker.unlink()
      print(f"Removed: {marker}")
      
    print("Cleanup completed")
    
  except Exception as e:
    print(f"Warning: Cleanup failed: {e}")