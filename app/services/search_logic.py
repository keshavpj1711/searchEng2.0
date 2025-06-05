from typing import List, Dict, Any
from app.services.build_inv_index import get_inverted_index
from app.services.tfidf import preprocess_text
from app.db.database_utils import fetch_documents_by_ids

def search_terms(query_terms: List[str]) -> Dict[int, float]:
  """
  Search for docs containing query terms and return relevance scores
  Returns: {doc_id: combined_relevance_score}
  combined_relvance_score: is found adding the scores currently for seperate tokens in your query
  """
  inverted_index = get_inverted_index()
  if not inverted_index:
    return {}
  
  document_scores: Dict[int, float] = {}
  
  for term in query_terms:
    if term in inverted_index:
      for doc_id, tf_idf_score in inverted_index[term]:
        if doc_id not in document_scores:
          document_scores[doc_id] = 0.0
        document_scores[doc_id] += tf_idf_score
  
  return document_scores


def get_document_details(document_scores: Dict[int, float], limit: int = 10) -> List[Dict[str, Any]]:
  """
  Convert document scores to actual document details
  Why: Users need to see title, URL, content - not just doc IDs and scores
  """
  if not document_scores:
    return []
  
  # Sort by relevance score (highest first) and limit results
  sorted_docs = sorted(document_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
  doc_ids = [doc_id for doc_id, score in sorted_docs]
  
  # Fetch actual document data from database
  documents = fetch_documents_by_ids(doc_ids)
  
  # Combine document data with relevance scores
  doc_lookup = {doc['id']: doc for doc in documents}
  
  results = []
  for doc_id, relevance_score in sorted_docs:
    if doc_id in doc_lookup:
      doc = doc_lookup[doc_id]
      results.append({
        "id": doc['id'],
        "title": doc['title'],
        "url": doc['url'],
        "content_preview": doc['content'],
        "relevance_score": round(relevance_score, 4)
      })
  
  return results


def perform_search(query: str, limit: int = 10) -> Dict[str, Any]:
  """
  Main search function that handles the complete search process
  Why: This combines query processing + searching + getting document details
  """
  # Preprocess the query (same as documents)
  query_terms = preprocess_text(query)
  if not query_terms:
    return {
      "query_received": query,
      "results_found": 0,
      "search_results": []
    }
  
  # Search using inverted index
  document_scores = search_terms(query_terms)
  
  # Get actual document details with scores
  search_results = get_document_details(document_scores, limit)
  
  return {
    "query_received": query,
    "results_found": len(search_results),
    "search_results": search_results
  }
