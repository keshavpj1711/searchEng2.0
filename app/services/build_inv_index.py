# Structure of inverted index we are trying to build 
# term -> [(doc_id, tf_idf_score),(doc_id, tf_idf_score),(doc_id, tf_idf_score),...]

from typing import Dict, List, Tuple
from app.db.database_utils import fetch_all_articles 
from app.services.tfidf import preprocess_text, calculate_tfidf
from app.services.build_tfidf_data import get_tfidf_data

# Global inverted index
# Later on we will keep in this in some sort of file or mem to be easily accessible 
# rather than recreating it on every server restart
inverted_index: Dict[str, List[Tuple[int, float]]] = {}

def build_inverted_index():
  """Build the inverted index using existing TF-IDF data"""
  global inverted_index
  
  print("Building inverted index...")
  
  # Get pre-calculated IDF scores
  tfidf_data = get_tfidf_data()
  if not tfidf_data['idf_scores']:
    print("No TF-IDF data available. Run build_tfidf_data first!")
    return
  
  # Fetch all articles using the database utility
  all_articles = fetch_all_articles()
  
  for article in all_articles:
    doc_id = article['id']
    
    # Same business logic: combine title and content
    combined_text = f"{article['title']} {article['title']} {article['content']}"
    tokens = preprocess_text(combined_text)
    tfidf_scores = calculate_tfidf(tokens, tfidf_data['idf_scores'])  # From our tfidf.py
    
    # Build inverted index
    for term, tf_idf_score in tfidf_scores.items():
      if term not in inverted_index:
        inverted_index[term] = []
      inverted_index[term].append((doc_id, tf_idf_score))
    
    print(f"Processed document {doc_id}: '{article['title'][:50]}...'")
  
  # Sort postings by TF-IDF score (highest first)
  
  # This is a very important part of building an efficient inverted index. 
  # What is code does is for a single term it sorts it's list in descending order according the tf_idf scores
  # This gives us an idea of which document has the highest tf_idf score for that term
  for term in inverted_index:
    inverted_index[term].sort(key=lambda x: x[1], reverse=True)

  
  print(f"Inverted index built with {len(inverted_index)} terms")
