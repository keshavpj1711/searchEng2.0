from typing import Dict, List
from app.db.database_utils import get_db_connection
from app.services.tfidf import preprocess_text, calculate_idf_with_freq
from app.db.database_utils import fetch_all_articles

# Setting as global vars later we can store it using Redis
total_document_count: int = 0
document_frequencies: Dict[str, int] = {}  # df_t: how many docs contain each term
idf_scores: Dict[str, float] = {}  # current IDF scores

def build_tfidf_data():
  """Build all TF-IDF related data structures"""
  global total_document_count, document_frequencies, idf_scores
  
  print("Fetching articles from database...")
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