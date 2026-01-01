import re
import math
import json
from collections import defaultdict, Counter
from config import INDEX_FILE


class SearchEngine:
    """Indexes and searches documents using TF-IDF"""
    
    def __init__(self):
        self.documents = []
        self.inverted_index = defaultdict(list)
        self.doc_count = 0
        self.idf_scores = {}
        
    def tokenize(self, text):
        """Convert text into tokens (words)"""
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def build_index(self, documents):
        """Build inverted index from documents"""
        print("Building search index...")
        self.documents = documents
        self.doc_count = len(documents)
        
        # Build inverted index
        for doc_id, doc in enumerate(documents):
            text = doc['title'] + ' ' + doc['content']
            tokens = self.tokenize(text)
            
            # Count term frequencies
            term_freq = Counter(tokens)
            
            # Add to inverted index
            for term, freq in term_freq.items():
                self.inverted_index[term].append({
                    'doc_id': doc_id,
                    'tf': freq
                })
        
        # Calculate IDF scores
        for term, postings in self.inverted_index.items():
            doc_freq = len(postings)
            self.idf_scores[term] = math.log(self.doc_count / doc_freq)
        
        print(f"Index built with {len(self.inverted_index)} unique terms!")
    
    def calculate_tf_idf(self, term, doc_id):
        """Calculate TF-IDF score for a term in a document"""
        if term not in self.inverted_index:
            return 0
        
        # Find term frequency for this document
        tf = 0
        for posting in self.inverted_index[term]:
            if posting['doc_id'] == doc_id:
                tf = posting['tf']
                break
        
        if tf == 0:
            return 0
        
        # TF-IDF = TF * IDF
        idf = self.idf_scores[term]
        return tf * idf
    
    def search(self, query, top_k=10):
        """Search for documents matching the query"""
        query_tokens = self.tokenize(query)
        
        if not query_tokens:
            return []
        
        # Calculate scores for each document
        scores = defaultdict(float)
        
        for term in query_tokens:
            if term in self.inverted_index:
                for posting in self.inverted_index[term]:
                    doc_id = posting['doc_id']
                    scores[doc_id] += self.calculate_tf_idf(term, doc_id)
        
        # Sort by score
        ranked_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top results
        results = []
        for doc_id, score in ranked_docs[:top_k]:
            doc = self.documents[doc_id]
            results.append({
                'url': doc['url'],
                'title': doc['title'],
                'snippet': doc['content'][:200] + '...',
                'score': score
            })
        
        return results
    
    def save_index(self, filename=INDEX_FILE):
        """Save index to disk"""
        data = {
            'documents': self.documents,
            'inverted_index': dict(self.inverted_index),
            'idf_scores': self.idf_scores
        }
        with open(filename, 'w') as f:
            json.dump(data, f)
        print(f"Index saved to {filename}")
    
    def load_index(self, filename=INDEX_FILE):
        """Load index from disk"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.documents = data['documents']
        self.inverted_index = defaultdict(list, data['inverted_index'])
        self.idf_scores = data['idf_scores']
        self.doc_count = len(self.documents)
        print(f"Index loaded from {filename}")
