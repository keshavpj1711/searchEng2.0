# App Structure 

```
search_engine_project/
├── app/                      # Main application source code
│   ├── __init__.py
│   ├── main.py               # FastAPI app instantiation and core API endpoints
│   ├── core/                 # Configuration and core settings
│   │   ├── __init__.py
│   │   └── config.py         # Application settings (e.g., database file path)
│   ├── db/                   # Database related files
│   │   ├── __init__.py
│   │   └── database_utils.py # Functions for SQLite connection and setup
│   ├── models/               # Pydantic models for request/response validation
│   │   ├── __init__.py
│   │   └── article.py        # Pydantic schema for Article data
│   ├── services/             # Business logic (search, indexing)
│   │   ├── __init__.py
│   │   └── search_logic.py   # Will hold search and indexing logic later
│   └── tasks/                # For Celery tasks (you'll add this later)
│       └── __init__.py
├── data/                     # To store your SQLite database file
│   └── wikipedia_articles.db
├── tests/                    # For your tests
│   └── __init__.py
├── .env                      # For environment variables (good practice)
├── .env.example              # Example of .env
├── .gitignore
├── requirements.txt
├── Dockerfile                # You'll add this on Day 5
├── docker-compose.yml        # You'll add this on Day 5
└── README.md

```

# Models

## Defining our document model: 

- ArticleBase defines common fields.

- ArticleCreate is what your API will expect in the body of the POST request to /documents.

- Article is what your API will return after successfully "creating" an article.

# Docker 

Docker is like a shipping container for your applications. Just like how a shipping container can hold anything and and work on any ship, truck or train, Docker containers can too hold your applications and run them on any computers.

## Key Concepts 

### Container v/s Image

- **Docker Image:** A blueprint for your app, basically it stores all the starting up steps to build your app and get it running

- **Docker Container:** The actual running through docker is known as Docker Container 

> So basically Image is the recipe and running that recipe is Container 

### Why Docker❓

What happens without Docker:

- Your Computer: Python 3.9, Redis installed, your search engine works ✅
- Friend's Computer: Python 3.8, no Redis, different OS ❌ Doesn't work!

> Production Server: Different setup ❌ Might not work!

With Docker: 

- Your Computer: Docker container with everything ✅
- Friend's Computer: Same Docker container ✅ Works!

> Production Server: Same Docker container ✅ Works!

### Dockerfile

A Dockerfile is like a recipe which tells Docker how to build your container

```docker
# Start with Python 
FROM python:3.9-slim

# Set up workspace 
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies 
RUN pip install -r requirements.txt

# Copy your app 
COPY . .

# Tell Docker what to run 
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Now since our application needs several services to be running at once we can use Docker Compose

### Docker Compose - Multiple Containers

Our Search Engine needs: 
- FAST API server
- Redis Server
- Maybe a database (if we use something other than SQLite)

Docker Compose let's us run multiple containers at once 

```yml
# docker-compose.yml
services:
  # Your FastAPI search engine
  web:
    build: .
    ports:
      - "8000:8000"
  
  # Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### How this helps our setup?

**With Docker:**

- Redis automatically starts with your app
- Everything is packaged together
- Runs the same everywhere
- One command to start everything: `docker-compose up`

### Basic Docker commands we will come across

```bash 
# Build an image from Dockerfile
docker build -t my-search-engine .

# Run a container
docker run -p 8000:8000 my-search-engine

# See running containers
docker ps

# Stop containers
docker-compose down

# Start everything
docker-compose up
```


# Celery

- Celery is a distributed task queue that helps you run tasks outside your main FastAPI application. 
- Think of it as a separate worker that handles time-consuming jobs in the background.

## Why Celery❓

Let's try to understand it with the help of an analogy:

**Imagine a restraunt:** 

- FAST API app -> Waiter (takes order and serves the customers)
- Celery worker -> Kitchen Chef (does the actual cooking in the bg)
- Redis -> Order Board (where orders are written for chef to see)

**With out celery**

```text 
Customer orders food → Waiter goes to kitchen and cooks → Customer waits 30 minutes → Other customers get angry
```

**With celery**

```text 
Customer orders food → Waiter writes order on board → Returns immediately to serve other customers
Meanwhile: Chef sees order on board → Cooks food → Food ready
```

## Where will we use Celery❓

When a new document is added the tfidf_data and the inv_index has to be rebuild again. This takes time and makes our app unable to handle other requests while this is done.

So as soon as a new document is added the celery worker is assigned to start rebuilding the required data but this is done in the backend and does not effect the actual working of our FAST API app which is still available to cater to user's requests.

> A Question that comes to my mind is: How does large scale systems handles these requests like these doesn't these lead to so many background tasks queuing with a large userbase?

