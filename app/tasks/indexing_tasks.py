from app.celery_app import celery_app
from app.services.build_tfidf_data import build_tfidf_data
from app.services.build_inv_index import build_inverted_index

@celery_app.task
def update_search_index():
  print("Celery: Rebuilding TF-IDF data and inverted index...")
  build_tfidf_data()
  build_inverted_index()
  print("Celery: Search index rebuilt.")


if __name__ == "__main__":
  
  print(type(update_search_index))  # Should show <class 'celery.app.task.Task'>
  print(hasattr(update_search_index, 'delay'))  # Should print True