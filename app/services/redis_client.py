import redis
from typing import Optional, Dict, Tuple

from redis import client
from app.core.config import settings
import pickle

# Global redis connection 
redis_client: Optional[redis.Redis] = None  # For current scenario we set it to None when no client is created it's just a good practice

# Why we are creating only a single instance of redis client and not seperate redis client for different datas, because
# - Each redis connection req memory and assets
# - Creating a new connection takes time

def get_redis_client() -> redis.Redis:
  """Get Redis client connection"""
  global redis_client
  if redis_client is None:
    try:
      redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=False  
        # This is set to false since we will store dicts directly 
        # the problem is when we store dicts in redis we need to serialize them first 
        # since, redis only stores strings/bytes, therefore what we do is 
        # we dump the dicts into pickle which stores in bytes and then we store the bytes(which contain the whole dict)
        # in redis directly
      )
      # Tests the connection
      redis_client.ping()
      print("Redis connection established successfully")
    except Exception as e:
      print(f"Redis connection failed: {e}")
      redis_client = None
  return redis_client


import pickle
from typing import Dict, Tuple

def save_tfidf_data_to_redis(total_docs: int, doc_frequencies: Dict[str, int], idf_scores: Dict[str, float]) -> bool:
  """Save TF-IDF data to Redis"""
  try: 
    client = get_redis_client()
    if client is None: 
      print("Redis client is not available")
      return False

    # Saving each component
    client.set("tfidf:total_documents", total_docs)
    # using pickle.dumps() to directly convert whole dict to bytes and save to redis 
    # since redis only stores string or bytes 
    client.set("tfidf:document_frequencies", pickle.dumps(doc_frequencies))
    client.set("tfidf:idf_scores", pickle.dumps(idf_scores))

    print(f"Saved TF-IDF data to Redis: {total_docs} docs, {len(idf_scores)} terms")
    return True

  except Exception as e:
    print(f"Error saving TF-IDF data to Redis: {e}")
    return False
    

def load_tfidf_data_from_redis() -> Tuple[int, Dict[str, int], Dict[str, float]]:
  """Load TF-IDF data from Redis"""
  try:
    client = get_redis_client()
    if client is None:
      print("Redis client not available")
      return 0, {}, {}
    
    # Check if all data exists
    if not all([
      client.exists("tfidf:total_documents"),
      client.exists("tfidf:document_frequencies"), 
      client.exists("tfidf:idf_scores")
    ]):
      print("TF-IDF data not found in Redis")
      return 0, {}, {}
    
    # Loading each component
    total_docs = int(client.get("tfidf:total_documents"))
    doc_frequencies = pickle.loads(client.get("tfidf:document_frequencies"))
    idf_scores = pickle.loads(client.get("tfidf:idf_scores"))
    
    print(f"Loaded TF-IDF data from Redis: {total_docs} docs, {len(idf_scores)} terms")
    return total_docs, doc_frequencies, idf_scores
    
  except Exception as e:
    print(f"Error loading TF-IDF data from Redis: {e}")
    return 0, {}, {}
