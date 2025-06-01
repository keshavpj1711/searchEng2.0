# Crawler: Wikipedia Featured Article Fetcher

This component (`app/crawler/crawler.py`) is responsible for fetching featured articles from Wikipedia. It gathers their titles, URLs, and main textual content, preparing a sample set of documents for the search engine.

## Key Features

* **Fetches Article Lists:**
    * Downloads the latest list of all featured articles from Wikipedia.
    * Alternatively, uses a locally cached list (`data/featured_articles_list.json`) for speed.
    * Saves the full list (titles \& URLs) to `data/featured_articles_list.json`.
* **User-Defined Sampling:**
    * To ensure a diverse sample, you'll be asked how many articles you want to process.
    * It then uses a systematic sampling method (e.g., picking every Nth article) to select a representative subset from the full list.
* **Content Extraction:**
    * Asynchronously fetches the full HTML for each sampled article.
    * Parses the HTML to extract the main text content, primarily from paragraph tags within the article body.
* **Output:**
    * Saves the sampled articles (title, URL, content, and a `retrieved_at` UTC timestamp) to `data/fetched_sample_articles.json`.
    * This JSON file provides the "Sample Documents" for the search engine.


## How to Run

1. Ensure all dependencies (`requests`, `aiohttp`, `beautifulsoup4`) are installed.
2. Navigate to the project root directory (`search_engine_project/`).
3. Run the script as a module:

```bash
python -m app.crawler.crawler
```

You will be prompted for choices regarding updating the article list and the number of samples to fetch.

## Design Notes \& Future Scalability

* **Intermediate JSON File:** For our current development stage (Day 1 ), producing `data/fetched_sample_articles.json` is useful. It provides:
    * A stable, inspectable set of "Sample Documents."
    * Decoupling of the crawling and ingestion processes.
* **Future Enhancement (Direct to DB):**
    * As you pointed out, for continuous or large-scale crawling (beyond the initial ~1000 sample articles), directly inserting fetched articles into the database (SQLite, then PostgreSQL) would be more efficient. This avoids large intermediate JSON files.
    * This direct-to-DB approach would involve the crawler calling database functions or API endpoints after fetching each article, which is a common pattern for more mature systems.

