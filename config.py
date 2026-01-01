# Crawling settings
MAX_PAGES = 50
CRAWL_DELAY = 1  # seconds between requests
REQUEST_TIMEOUT = 10  # seconds

# Seed URLs to start crawling
SEED_URLS = [
    'https://en.wikipedia.org/wiki/Search_engine',
    'https://en.wikipedia.org/wiki/Python_(programming_language)',
    'https://en.wikipedia.org/wiki/Web_crawler',
    'https://en.wikipedia.org/wiki/Information_retrieval',
]

# Index storage
INDEX_FILE = 'search_index.json'

# Web server settings
HOST = '0.0.0.0'
PORT = 5000
DEBUG = False

# User agent for crawler
USER_AGENT = 'SimpleSearchBot/1.0 (Educational Project)'
