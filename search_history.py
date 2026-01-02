import json
import os
from datetime import datetime
from collections import deque

HISTORY_FILE = 'search_history.json'
MAX_HISTORY_SIZE = 50


class SearchHistory:
    """Manage search history functionality"""
    
    def __init__(self):
        self.history = deque(maxlen=MAX_HISTORY_SIZE)
        self.load_history()
    
    def add_search(self, query, results_count):
        """Add a search to history"""
        if not query.strip():
            return
        
        search_entry = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'results_count': results_count
        }
        
        # Remove duplicate queries and add to front
        self.history = deque([x for x in self.history if x['query'] != query], maxlen=MAX_HISTORY_SIZE)
        self.history.appendleft(search_entry)
        self.save_history()
    
    def get_recent_searches(self, limit=10):
        """Get recent searches"""
        return list(self.history)[:limit]
    
    def get_popular_queries(self, limit=10):
        """Get most frequently searched queries"""
        query_counts = {}
        for entry in self.history:
            query = entry['query']
            query_counts[query] = query_counts.get(query, 0) + 1
        
        sorted_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)
        return [query for query, count in sorted_queries[:limit]]
    
    def clear_history(self):
        """Clear all search history"""
        self.history.clear()
        self.save_history()
    
    def save_history(self):
        """Save history to file"""
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(list(self.history), f)
        except Exception as e:
            print(f"Error saving search history: {e}")
    
    def load_history(self):
        """Load history from file"""
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    history_data = json.load(f)
                    self.history = deque(history_data, maxlen=MAX_HISTORY_SIZE)
        except Exception as e:
            print(f"Error loading search history: {e}")
            self.history = deque(maxlen=MAX_HISTORY_SIZE)
