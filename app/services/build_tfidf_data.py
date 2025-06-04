from typing import Dict, List
from app.db.database_utils import get_db_connection
from app.services.tfidf import preprocess_text, calculate_idf_with_freq

# Setting as global vars later we can store it using Redis
total_document_count: int = 0
document_frequencies: Dict[str, int] = {}  # df_t: how many docs contain each term
idf_scores: Dict[str, float] = {}  # current IDF scores

# Fetching all docs from db
# This step may or may not be present depending upon 
# If the IDF scores and doc frequencies are updated after addition of every doc or not
def fetch_all_documents_from_db() -> List[str]:
  """Fetch all document contents from the database"""
  contents = []
  try:
    with get_db_connection() as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT title, content FROM articles WHERE content IS NOT NULL")
      rows = cursor.fetchall()
      for row in rows:
        # Combine title and content into one document, giving title extra weight
        combined_text = f"{row['title']} {row['title']} {row['content']}"
        contents.append(combined_text)
  except Exception as e:
    print(f"Error fetching documents: {e}")
  return contents


def build_tfidf_data():
  """Build all TF-IDF related data structures"""
  global total_document_count, document_frequencies, idf_scores
  
  print("Fetching documents from database...")
  all_contents = fetch_all_documents_from_db()
  
  if not all_contents:
    print("No documents found in database!")
    return

  print(f"Found {len(all_contents)} documents. Processing...")

  # Preprocess all documents to get tokens
  corpus_tokens = []
  for content in all_contents:
    tokens = preprocess_text(content)
    corpus_tokens.append(tokens)

  # total document count
  total_document_count = len(corpus_tokens)

  # IDF scores and document frequencies
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