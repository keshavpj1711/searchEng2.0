from typing import Dict, List
from app.db.database_utils import fetch_all_articles
from app.services.tfidf import preprocess_text, calculate_idf_with_freq
from app.services.redis_client import save_tfidf_data_to_redis, load_tfidf_data_from_redis

# Setting as global vars later we can store it using Redis
total_document_count: int = 0
document_frequencies: Dict[str, int] = {}  # df_t: how many docs contain each term
idf_scores: Dict[str, float] = {}  # current IDF scores

def build_tfidf_data():
  """Build all TF-IDF related data structures"""
  global total_document_count, document_frequencies, idf_scores
  
  # Try to load from Redis first
  print("Checking Redis for cached TF-IDF data...")
  cached_total, cached_doc_freq, cached_idf = load_tfidf_data_from_redis()
  
  if cached_total > 0 and cached_doc_freq and cached_idf:
    # Data found in Redis - using it!
    total_document_count = cached_total
    document_frequencies = cached_doc_freq
    idf_scores = cached_idf
    print("Using cached TF-IDF data from Redis")
    return
  
  # No cached data found - build from scratch
  print("No cached data found. Building TF-IDF data from database...")
  all_articles = fetch_all_articles() 
  
  if not all_articles:
    print("No articles found in database!")
    return

  print(f"Found {len(all_articles)} articles. Processing...")

  # Process articles to create combined content for TF-IDF
  corpus_tokens = []
  for article in all_articles:
    # Combining title and content to give title extra weight
    combined_text = f"{article['title']} {article['title']} {article['content']}"
    tokens = preprocess_text(combined_text)
    corpus_tokens.append(tokens)

  total_document_count = len(corpus_tokens)
  idf_scores, document_frequencies = calculate_idf_with_freq(corpus_tokens)

  print(f"Built TF-IDF data:")
  print(f"  - Total documents: {total_document_count}")
  print(f"  - Unique terms: {len(idf_scores)}")

  # Save to Redis for next time
  print("Saving TF-IDF data to Redis...")
  save_tfidf_data_to_redis(total_document_count, document_frequencies, idf_scores)


def get_tfidf_data():
  """Return the current TF-IDF data structures"""
  return {
    'total_documents': total_document_count,
    'document_frequencies': document_frequencies,
    'idf_scores': idf_scores
  }


if __name__ == "__main__":
  # Test the function
  build_tfidf_data()
  data = get_tfidf_data()
  print(f"\nSample IDF scores (first 5):")
  for i, (term, score) in enumerate(data['idf_scores'].items()):
    if i >= 5:
      break
    print(f"  {term}: {score:.4f}")