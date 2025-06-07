import os
from celery import Celery
from app.core.config import settings

# For Docker: Use internal container communication
# For local dev: Use external port mapping
redis_host = os.getenv('REDIS_HOST', settings.REDIS_HOST)
redis_port = os.getenv('REDIS_PORT', settings.REDIS_PORT)
redis_db = os.getenv('REDIS_DB', settings.REDIS_DB)

redis_url = f'redis://{redis_host}:{redis_port}/{redis_db}'

celery_app = Celery(
  "search_engine",
  broker=redis_url,
  backend=redis_url,
  include=['app.tasks.indexing_tasks']
)

celery_app.autodiscover_tasks(['app.tasks'])
