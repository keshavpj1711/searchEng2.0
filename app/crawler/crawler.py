import requests
import json
import asyncio
import aiohttp
from aiohttp import ClientTimeout, ClientError
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone

# --- Configuration ---
URL_WIKI = "https://en.wikipedia.org"
URL_FEAT_ARTICLES = "https://en.wikipedia.org/wiki/Wikipedia:Featured_articles"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

# Path Setup
try:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
except NameError:
    PROJECT_ROOT = os.path.abspath(".")

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

FEATURED_ARTICLES_LIST_PATH = os.path.join(DATA_DIR, "featured_articles_list.json")
FETCHED_SAMPLE_ARTICLES_PATH = os.path.join(DATA_DIR, "fetched_sample_articles.json")

# --- Improved Helper Functions with Retry Logic ---
async def scrap_article_content(session, url, title, max_retries=3):
    """Fetches and extracts content for a single Wikipedia article with retry logic."""
    print(f"Fetching content for: {title}")
    
    for attempt in range(1, max_retries + 1):
        try:
            # Set timeout for this specific request
            timeout = ClientTimeout(
                total=30,      # Total timeout: 30 seconds
                connect=10,    # Connection timeout: 10 seconds
                sock_read=20   # Socket read timeout: 20 seconds
            )
            
            async with session.get(url, headers=HEADERS, timeout=timeout) as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, "html.parser")
                
                content_div = soup.find("div", id="mw-content-text")
                article_text = ""
                if content_div:
                    paragraphs = content_div.find_all("p")
                    for p in paragraphs:
                        article_text += p.get_text(separator=" ", strip=True) + "\n\n"
                
                if not article_text.strip():
                    print(f"Warning: No paragraph text extracted for {title}")

                retrieved_at_utc = datetime.now(timezone.utc).isoformat()
                
                print(f"Successfully fetched: {title}")
                return {
                    "title": title,
                    "url": url,
                    "content": article_text.strip() if article_text else None,
                    "retrieved_at": retrieved_at_utc
                }
                
        except (ClientError, asyncio.TimeoutError) as e:
            print(f"Attempt {attempt}/{max_retries} failed for {title}: {type(e).__name__}")
            if attempt == max_retries:
                print(f"All {max_retries} attempts failed for {title}")
                return {
                    "title": title, 
                    "url": url, 
                    "content": None, 
                    "retrieved_at": None, 
                    "error": f"Failed after {max_retries} attempts: {str(e)}"
                }
            
            # Exponential backoff: wait longer between retries
            wait_time = 2 ** attempt  # 2, 4, 8 seconds
            print(f"⏳ Waiting {wait_time} seconds before retry...")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            print(f"Unexpected error scraping {title}: {e}")
            return {
                "title": title, 
                "url": url, 
                "content": None, 
                "retrieved_at": None, 
                "error": str(e)
            }

async def fetch_content_for_articles_async(articles_to_fetch_list):
    """Asynchronously fetches content with improved concurrency control and error handling."""
    fetched_data = []
    
    # Reduce concurrency to avoid overwhelming Wikipedia
    semaphore = asyncio.Semaphore(5)  # Only 5 concurrent requests
    
    # Set session-level timeout and connection limits
    timeout = ClientTimeout(total=60)  # Overall session timeout
    connector = aiohttp.TCPConnector(
        limit=20,           # Total connection pool size
        limit_per_host=5,   # Max connections per Wikipedia
        ttl_dns_cache=300,  # DNS cache TTL (5 minutes)
        use_dns_cache=True,
        enable_cleanup_closed=True
    )
    
    async with aiohttp.ClientSession(
        timeout=timeout, 
        connector=connector,
        headers=HEADERS
    ) as session:
        
        async def sem_fetch(article_info):
            """Fetch with semaphore control"""
            async with semaphore:
                return await scrap_article_content(
                    session, 
                    article_info["link"], 
                    article_info["title"]
                )
        
        # Process in smaller batches to avoid overwhelming the server
        batch_size = 100
        total_batches = (len(articles_to_fetch_list) + batch_size - 1) // batch_size
        
        for i in range(0, len(articles_to_fetch_list), batch_size):
            batch = articles_to_fetch_list[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"Processing batch {batch_num}/{total_batches}: {len(batch)} articles")
            
            tasks = [sem_fetch(article_info) for article_info in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful = 0
            failed = 0
            for result in results:
                if isinstance(result, Exception):
                    print(f"Task failed with exception: {result}")
                    failed += 1
                elif result and result.get("content") is not None:
                    fetched_data.append(result)
                    successful += 1
                elif result:
                    print(f"No content for: {result.get('title', 'Unknown')} - {result.get('error', 'Content was None')}")
                    failed += 1
            
            print(f"Batch {batch_num} complete: {successful} successful, {failed} failed")
            
            # Add delay between batches to be respectful to Wikipedia
            if i + batch_size < len(articles_to_fetch_list):
                print("⏳ Waiting 3 seconds before next batch...")
                await asyncio.sleep(3)
    
    print(f"\nFetching complete! Successfully retrieved {len(fetched_data)} articles")
    return fetched_data

# --- Sync helper functions for setup script (unchanged) ---
def get_featured_articles_list_sync():
    """Sync function to get featured articles list"""
    print("\nStep 1: Get list of all featured articles.")
    print(f"1. Fetch list of articles from Wikipedia (fetches {URL_FEAT_ARTICLES})")
    print(f"2. Use existing local list (from {FEATURED_ARTICLES_LIST_PATH})")
    
    choice = input("Choose option (1 or 2): ")

    if choice == '1':
        try:
            print(f"Fetching featured articles list from {URL_FEAT_ARTICLES}...")
            response = requests.get(URL_FEAT_ARTICLES, headers=HEADERS)
            response.raise_for_status()
            print("Successfully connected to Wikipedia featured articles page.")

            soup = BeautifulSoup(response.text, "html.parser")
            feat_article_spans = soup.find_all('span', class_='featured_article_metadata has_been_on_main_page')
            
            current_articles_list = []
            for span in feat_article_spans:
                if span.a and span.a.has_attr('href') and span.a.text:
                    current_articles_list.append({
                        "title": span.a.text.strip(),
                        "link": URL_WIKI + span.a["href"]
                    })
            
            with open(FEATURED_ARTICLES_LIST_PATH, "w", encoding="utf-8") as f:
                json.dump(current_articles_list, f, indent=4, ensure_ascii=False)
            print(f"Found {len(current_articles_list)} featured articles. List saved to '{FEATURED_ARTICLES_LIST_PATH}'.")
            return current_articles_list
        except requests.RequestException as e:
            print(f"Error fetching from Wikipedia: {e}. Attempting to use local list if available.")
            choice = '2'  # Fallback to using local list
        except Exception as e:
            print(f"An unexpected error occurred during Wikipedia list fetch: {e}. Exiting.")
            return []

    if choice == '2':
        try:
            with open(FEATURED_ARTICLES_LIST_PATH, "r", encoding="utf-8") as f:
                all_featured_articles = json.load(f)
            print(f"Loaded {len(all_featured_articles)} articles from '{FEATURED_ARTICLES_LIST_PATH}'.")
            return all_featured_articles
        except FileNotFoundError:
            print(f"Local list '{FEATURED_ARTICLES_LIST_PATH}' not found. Please run option 1 first. Exiting.")
            return []
        except json.JSONDecodeError:
            print(f"Error decoding JSON from '{FEATURED_ARTICLES_LIST_PATH}'. File may be corrupt. Exiting.")
            return []

def sample_articles_sync(all_featured_articles):
    """Sync function to handle user input and sampling"""
    print(f"\nStep 2: Select articles for content fetching (sampling).")
    total_available = len(all_featured_articles)
    while True:
        try:
            num_samples_desired = int(input(f"Out of {total_available} articles, how many do you want to fetch content for? "))
            if 0 < num_samples_desired <= total_available:
                break
            elif num_samples_desired == 0:
                print("Number of samples cannot be zero. Please enter a valid number.")
            else:
                print(f"Please enter a number between 1 and {total_available}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    sampled_articles_to_fetch = []
    if num_samples_desired == total_available:
        sampled_articles_to_fetch = all_featured_articles
        print(f"Selected all {total_available} articles for content fetching.")
    else:
        interval = max(1, total_available // num_samples_desired)
        for i in range(0, total_available, interval):
            if len(sampled_articles_to_fetch) < num_samples_desired:
                sampled_articles_to_fetch.append(all_featured_articles[i])
            else:
                break
        
        idx = 0
        while len(sampled_articles_to_fetch) < num_samples_desired and idx < total_available:
            if all_featured_articles[idx] not in sampled_articles_to_fetch:
                 sampled_articles_to_fetch.append(all_featured_articles[idx])
            idx += 1

        print(f"Selected {len(sampled_articles_to_fetch)} articles for content fetching using systematic sampling.")

    return sampled_articles_to_fetch

def save_articles_to_json_sync(articles_with_content):
    """Sync function to save articles to JSON"""
    print(f"\nStep 4: Saving fetched article content.")
    if articles_with_content:
        with open(FETCHED_SAMPLE_ARTICLES_PATH, "w", encoding="utf-8") as f:
            json.dump(articles_with_content, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved content for {len(articles_with_content)} articles to '{FETCHED_SAMPLE_ARTICLES_PATH}'.")
        print("Each article includes: title, url, content, retrieved_at.")
    else:
        print(f"No content was successfully fetched for any of the selected sample articles. '{FETCHED_SAMPLE_ARTICLES_PATH}' not created or updated.")

# --- Main Crawler Logic ---
async def run_crawler_operations_async():
    """Async version for use in FastAPI lifespan"""
    print("--- Wikipedia Featured Article Crawler ---")

    # Steps 1-2: Get featured articles and sample (sync operations)
    all_featured_articles = get_featured_articles_list_sync()
    if not all_featured_articles:
        print("No featured articles to process. Exiting.")
        return

    sampled_articles_to_fetch = sample_articles_sync(all_featured_articles)
    if not sampled_articles_to_fetch:
        print("No articles selected for sampling. Exiting.")
        return

    # Step 3: Fetch content (async operation with improved error handling)
    print(f"\nStep 3: Fetching content for {len(sampled_articles_to_fetch)} selected articles...")
    print("Using improved timeout handling and retry logic...")
    articles_with_content = await fetch_content_for_articles_async(sampled_articles_to_fetch)

    # Step 4: Save to JSON (sync operation)
    save_articles_to_json_sync(articles_with_content)
    
    print("\n--- Crawler operations complete ---")

def run_crawler_operations():
    """Original sync version for standalone script execution"""
    print("--- Wikipedia Featured Article Crawler ---")

    # Steps 1-2: Get featured articles and sample
    all_featured_articles = get_featured_articles_list_sync()
    if not all_featured_articles:
        print("No featured articles to process. Exiting.")
        return

    sampled_articles_to_fetch = sample_articles_sync(all_featured_articles)
    if not sampled_articles_to_fetch:
        print("No articles selected for sampling. Exiting.")
        return

    # Step 3: Fetch content (this uses asyncio.run for standalone execution)
    print(f"\nStep 3: Fetching content for {len(sampled_articles_to_fetch)} selected articles...")
    articles_with_content = asyncio.run(fetch_content_for_articles_async(sampled_articles_to_fetch))

    # Step 4: Save to JSON
    save_articles_to_json_sync(articles_with_content)
    
    print("\n--- Crawler operations complete ---")

# --- Entry Point ---
if __name__ == "__main__":
    run_crawler_operations()
