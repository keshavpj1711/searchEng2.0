import requests
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone # For retrieved_at timestamp

# --- Configuration ---
URL_WIKI = "https://en.wikipedia.org"
URL_FEAT_ARTICLES = "https://en.wikipedia.org/wiki/Wikipedia:Featured_articles"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

# Path Setup
# We want output files in search_engine_project/data/
try:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
except NameError: # __file__ is not defined if running in certain interactive environments
    PROJECT_ROOT = os.path.abspath(".") # Fallback to current working directory

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
# Ensure the main data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

FEATURED_ARTICLES_LIST_PATH = os.path.join(DATA_DIR, "featured_articles_list.json")
FETCHED_SAMPLE_ARTICLES_PATH = os.path.join(DATA_DIR, "fetched_sample_articles.json")


# --- Helper Functions ---
async def scrap_article_content(session, url, title):
    """Fetches and extracts content for a single Wikipedia article."""
    print(f"Fetching content for: {title} from {url}")
    try:
        async with session.get(url, headers=HEADERS) as response: # Pass headers here too
            response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
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
                # Return with empty content but mark as successful fetch for structure
                # Or, treat as an error if content is mandatory
                # For now, let's include it but a user might want to filter these out later.

            retrieved_at_utc = datetime.now(timezone.utc).isoformat()
            
            return {
                "title": title,
                "url": url,
                "content": article_text.strip() if article_text else None, # Store None if truly empty
                "retrieved_at": retrieved_at_utc
            }
    except aiohttp.ClientError as e:
        print(f"AIOHTTP ClientError scraping {title} at {url}: {e}")
        return {"title": title, "url": url, "content": None, "retrieved_at": None, "error": str(e)}
    except Exception as e:
        print(f"Generic error scraping {title} at {url}: {e}")
        return {"title": title, "url": url, "content": None, "retrieved_at": None, "error": str(e)}

async def fetch_content_for_articles_async(articles_to_fetch_list):
    """Asynchronously fetches content for a list of articles."""
    fetched_data = []
    # Create one session for all requests for better performance
    async with aiohttp.ClientSession() as session:
        tasks = []
        for article_info in articles_to_fetch_list:
            tasks.append(
                scrap_article_content(session, article_info["link"], article_info["title"])
            )
        
        # Use return_exceptions=True to handle individual task failures without stopping all
        results = await asyncio.gather(*tasks, return_exceptions=True) 
        
        for i, result in enumerate(results):
            original_article_info = articles_to_fetch_list[i]
            if isinstance(result, Exception):
                print(f"Task for '{original_article_info['title']}' failed with exception: {result}")
                # Optionally add error info to a results list
            elif result and result.get("content") is not None: # Check for non-empty content specifically
                fetched_data.append(result)
            elif result: # Result was returned, but content might be None or an error flag set
                print(f"No content fetched or error for: {result.get('title', original_article_info['title'])} - Error: {result.get('error', 'Content was None')}")
    return fetched_data

# --- Main Crawler Logic ---
def run_crawler_operations():
    """Orchestrates the crawling process."""
    print("--- Wikipedia Featured Article Crawler ---")

    # 1. Get the full list of featured articles (title & link)
    all_featured_articles = []
    print("\nStep 1: Get list of all featured articles.")
    print(f"1. Update list from Wikipedia (fetches {URL_FEAT_ARTICLES})")
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
            all_featured_articles = current_articles_list
            print(f"Found {len(all_featured_articles)} featured articles. List saved to '{FEATURED_ARTICLES_LIST_PATH}'.")
        except requests.RequestException as e:
            print(f"Error fetching from Wikipedia: {e}. Attempting to use local list if available.")
            if os.path.exists(FEATURED_ARTICLES_LIST_PATH):
                 choice = '2' # Fallback to using local list
            else:
                print("No local list available. Exiting.")
                return
        except Exception as e:
            print(f"An unexpected error occurred during Wikipedia list fetch: {e}. Exiting.")
            return


    if choice == '2': # Handles explicit choice '2' or fallback from failed '1'
        try:
            with open(FEATURED_ARTICLES_LIST_PATH, "r", encoding="utf-8") as f:
                all_featured_articles = json.load(f)
            print(f"Loaded {len(all_featured_articles)} articles from '{FEATURED_ARTICLES_LIST_PATH}'.")
        except FileNotFoundError:
            print(f"Local list '{FEATURED_ARTICLES_LIST_PATH}' not found. Please run option 1 first. Exiting.")
            return
        except json.JSONDecodeError:
            print(f"Error decoding JSON from '{FEATURED_ARTICLES_LIST_PATH}'. File may be corrupt. Exiting.")
            return

    if not all_featured_articles:
        print("No featured articles to process. Exiting.")
        return

    # 2. Ask user how many samples they want and perform systematic sampling
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
        # If interval math resulted in fewer than desired, try to fill up
        # This is a simple way, more complex might pick random remaining if needed
        idx = 0
        while len(sampled_articles_to_fetch) < num_samples_desired and idx < total_available:
            if all_featured_articles[idx] not in sampled_articles_to_fetch:
                 sampled_articles_to_fetch.append(all_featured_articles[idx])
            idx +=1

        print(f"Selected {len(sampled_articles_to_fetch)} articles for content fetching using systematic sampling.")

    if not sampled_articles_to_fetch:
        print("No articles selected for sampling. Exiting.")
        return

    # 3. Fetch content for the sampled articles
    print(f"\nStep 3: Fetching content for {len(sampled_articles_to_fetch)} selected articles...")
    # This part uses asyncio
    articles_with_content = asyncio.run(fetch_content_for_articles_async(sampled_articles_to_fetch))

    # 4. Save the fetched sample articles (with content)
    print(f"\nStep 4: Saving fetched article content.")
    if articles_with_content:
        with open(FETCHED_SAMPLE_ARTICLES_PATH, "w", encoding="utf-8") as f:
            json.dump(articles_with_content, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved content for {len(articles_with_content)} articles to '{FETCHED_SAMPLE_ARTICLES_PATH}'.")
        print("Each article includes: title, url, content, retrieved_at.")
    else:
        print(f"No content was successfully fetched for any of the selected sample articles. '{FETCHED_SAMPLE_ARTICLES_PATH}' not created or updated.")
    
    print("\n--- Crawler operations complete ---")

# --- Entry Point ---
if __name__ == "__main__":
    # To run this script:
    # 1. Make sure you are in the `search_engine_project` root directory.
    # 2. Run: `python -m app.crawler.crawler`
    # Ensure app/crawler/ has an __init__.py file (can be empty).
    run_crawler_operations()
