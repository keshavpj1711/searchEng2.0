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

