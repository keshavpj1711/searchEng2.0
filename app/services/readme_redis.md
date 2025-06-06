# Redis: Remote Dictionary Server

- Redis is an in-memory database that stores data in RAM, making it extremely fast to read and write data.
- It's basically a giant dict/hash table that lives in your PCs RAM.

## Redis for beginners

### Storing in Redis

Redis stores data as key-value pairs, just like Python dictionaries:

```python 
# Python dictionary (only in your program)
my_data = {"user:123": "John", "count": 42}

# Redis (shared across programs, survives restarts)
redis_client.set("user:123", "John")
redis_client.set("count", 42)
```

**Supported Datatypes**: Strings, Lists , Sets, Hashes

## Why we need this?

### Current Problem:

Everytime i restart my FASTAPI server it rebuilds: 

- **TF-IDF data** (total_document_count, document_frequencies, idf_scores)
- **Inverted index** (the big dictionary mapping terms to documents)

Rebuilding this unless data doesn't change is useless wastes time

## How is solving the above problem

Basically stores these files to be used by search logic and wherever necessary without rebuilding them

```python 
# Server restart:
# 1. Check Redis first
total_document_count = redis_client.get("tfidf:total_docs")  # Found instantly!
document_frequencies = redis_client.get("tfidf:doc_freq")   # Found instantly!
# No rebuilding needed!
```

## Why we are creating only a single instance of redis client?





