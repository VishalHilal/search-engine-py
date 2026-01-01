from crawler import WebCrawler
from indexer import SearchEngine
from web_app import run_app
from config import SEED_URLS, MAX_PAGES, INDEX_FILE


def main():
    print("=== Simple Web Search Engine ===\n")
    
    # Initialize search engine
    engine = SearchEngine()
    
    # Try to load existing index
    try:
        engine.load_index(INDEX_FILE)
        print("Using existing index.\n")
    except FileNotFoundError:
        print("No existing index found. Starting crawl...\n")
        
        # Crawl the web
        crawler = WebCrawler(max_pages=MAX_PAGES)
        documents = crawler.crawl(SEED_URLS)
        
        # Build search index
        engine.build_index(documents)
        
        # Save index for future use
        engine.save_index(INDEX_FILE)
    
    # Start web server
    run_app(engine)


if __name__ == '__main__':
    main()
