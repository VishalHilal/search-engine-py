import re
import math
import json
from collections import defaultdict, Counter
from config import INDEX_FILE


class QueryParser:
    """Parse advanced search queries with operators"""
    
    @staticmethod
    def parse_query(query):
        """Parse query with AND, OR, NOT, and phrase operators"""
        query = query.strip()
        
        # Handle quoted phrases first
        phrases = re.findall(r'"([^"]*)"', query)
        for phrase in phrases:
            query = query.replace(f'"{phrase}"', f'PHRASE_{len(phrases)-1}')
        
        # Split into tokens
        tokens = re.findall(r'\b\w+\b|[()]|AND|OR|NOT|PHRASE_\d+', query)
        
        # Replace phrase placeholders
        for i, phrase in enumerate(phrases):
            for j, token in enumerate(tokens):
                if token == f'PHRASE_{i}':
                    tokens[j] = phrase
        
        return tokens, phrases


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
        
        # Build domain and content type indexes for filtering
        self.build_filter_indexes()
        
        print(f"Index built with {len(self.inverted_index)} unique terms!")
    
    def build_filter_indexes(self):
        """Build indexes for filtering by domain, content type, and date"""
        self.domain_index = defaultdict(list)
        self.content_type_index = defaultdict(list)
        self.date_index = defaultdict(list)
        
        for doc_id, doc in enumerate(self.documents):
            metadata = doc.get('metadata', {})
            
            # Domain index
            domain = metadata.get('domain', 'unknown')
            self.domain_index[domain].append(doc_id)
            
            # Content type index
            content_type = metadata.get('content_type', 'text/html')
            self.content_type_index[content_type].append(doc_id)
            
            # Date index (by year and month)
            pub_date = metadata.get('publication_date')
            if pub_date:
                try:
                    # Extract year from date
                    year = pub_date.split('-')[0] if '-' in pub_date else pub_date.split('/')[-1]
                    self.date_index[year].append(doc_id)
                except:
                    pass
    
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
    
    def search(self, query, top_k=10, filters=None):
        """Search for documents matching the query with advanced operators and filters"""
        # Parse the query
        tokens, phrases = QueryParser.parse_query(query)
        
        # If no operators found, use simple search
        if not any(token in ['AND', 'OR', 'NOT', '(', ')'] for token in tokens) and not phrases:
            return self._simple_search(query, top_k, filters)
        
        # Advanced search with filters
        matching_docs = []
        
        # Apply filters first to get candidate documents
        candidate_docs = self.apply_filters(filters) if filters else set(range(len(self.documents)))
        
        for doc_id in candidate_docs:
            if self.evaluate_query(tokens, doc_id):
                # Calculate relevance score
                score = self._calculate_relevance_score(tokens, doc_id)
                matching_docs.append((doc_id, score))
        
        # Sort by score
        matching_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        results = []
        for doc_id, score in matching_docs[:top_k]:
            doc = self.documents[doc_id]
            results.append({
                'url': doc['url'],
                'title': doc['title'],
                'snippet': doc['content'][:200] + '...',
                'score': score,
                'metadata': doc.get('metadata', {})
            })
        
        return results
    
    def apply_filters(self, filters):
        """Apply filters to get candidate documents"""
        candidate_docs = set(range(len(self.documents)))
        
        # Domain filter
        if filters.get('domain'):
            domain_docs = set()
            for domain in filters['domain']:
                domain_docs.update(self.domain_index.get(domain, []))
            candidate_docs &= domain_docs
        
        # Content type filter
        if filters.get('content_type'):
            content_docs = set()
            for ctype in filters['content_type']:
                content_docs.update(self.content_type_index.get(ctype, []))
            candidate_docs &= content_docs
        
        # Date filter
        if filters.get('date'):
            date_docs = set()
            for date in filters['date']:
                date_docs.update(self.date_index.get(date, []))
            candidate_docs &= date_docs
        
        return candidate_docs
    
    def get_filter_options(self):
        """Get available filter options"""
        return {
            'domains': sorted(list(self.domain_index.keys())),
            'content_types': sorted(list(self.content_type_index.keys())),
            'dates': sorted(list(self.date_index.keys()), reverse=True)
        }
    
    def _simple_search(self, query, top_k=10, filters=None):
        """Original simple search implementation with filters"""
        query_tokens = self.tokenize(query)
        
        if not query_tokens:
            return []
        
        # Apply filters first
        candidate_docs = self.apply_filters(filters) if filters else set(range(len(self.documents)))
        
        # Calculate scores for each document
        scores = defaultdict(float)
        
        for term in query_tokens:
            if term in self.inverted_index:
                for posting in self.inverted_index[term]:
                    doc_id = posting['doc_id']
                    if doc_id in candidate_docs:  # Only consider filtered documents
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
                'score': score,
                'metadata': doc.get('metadata', {})
            })
        
        return results
    
    def _calculate_relevance_score(self, tokens, doc_id):
        """Calculate relevance score for advanced query"""
        score = 0.0
        doc_text = self.documents[doc_id]['title'] + ' ' + self.documents[doc_id]['content']
        doc_tokens = self.tokenize(doc_text)
        
        for token in tokens:
            if token not in ['AND', 'OR', 'NOT', '(', ')']:
                if ' ' in token:  # Phrase
                    if self.phrase_search(token, doc_id):
                        score += 5.0  # Bonus for phrase matches
                else:
                    if token.lower() in doc_tokens:
                        score += self.calculate_tf_idf(token.lower(), doc_id)
        
        return score
    
    def highlight_terms(self, text, query):
        """Highlight search terms in text"""
        tokens, phrases = QueryParser.parse_query(query)
        
        # Extract search terms (excluding operators)
        search_terms = []
        for token in tokens:
            if token not in ['AND', 'OR', 'NOT', '(', ')']:
                if ' ' in token:  # Phrase
                    search_terms.append(token.lower())
                else:
                    search_terms.append(token.lower())
        
        # Highlight terms in text
        highlighted_text = text
        for term in search_terms:
            if ' ' in term:  # Phrase
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted_text = pattern.sub(f'<mark>{term}</mark>', highlighted_text)
            else:
                pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                highlighted_text = pattern.sub(f'<mark>{term}</mark>', highlighted_text)
        
        return highlighted_text
    
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
    
    def get_suggestions(self, query, limit=10):
        """Get auto-complete suggestions based on indexed terms"""
        query = query.lower()
        suggestions = []
        
        # Find terms that start with the query
        for term in self.inverted_index.keys():
            if term.startswith(query) and len(term) > len(query):
                suggestions.append(term)
        
        # Sort by frequency (more common terms first)
        suggestions.sort(key=lambda x: len(self.inverted_index[x]), reverse=True)
        
        return suggestions[:limit]
    
    def phrase_search(self, phrase, doc_id):
        """Search for exact phrase in document"""
        doc = self.documents[doc_id]
        text = (doc['title'] + ' ' + doc['content']).lower()
        return phrase.lower() in text
    
    def evaluate_query(self, tokens, doc_id):
        """Evaluate parsed query against a document"""
        stack = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if token == '(':
                # Find matching closing parenthesis
                paren_count = 1
                j = i + 1
                while j < len(tokens) and paren_count > 0:
                    if tokens[j] == '(':
                        paren_count += 1
                    elif tokens[j] == ')':
                        paren_count -= 1
                    j += 1
                
                # Recursively evaluate sub-expression
                sub_tokens = tokens[i+1:j-1]
                result = self.evaluate_query(sub_tokens, doc_id)
                stack.append(result)
                i = j
            elif token == 'AND':
                if len(stack) >= 2:
                    right = stack.pop()
                    left = stack.pop()
                    stack.append(left and right)
                i += 1
            elif token == 'OR':
                if len(stack) >= 2:
                    right = stack.pop()
                    left = stack.pop()
                    stack.append(left or right)
                i += 1
            elif token == 'NOT':
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    if next_token in ['AND', 'OR', 'NOT', '(', ')']:
                        i += 1
                        continue
                    
                    # Check if next token exists in document
                    term_found = next_token.lower() in self.tokenize(
                        self.documents[doc_id]['title'] + ' ' + self.documents[doc_id]['content']
                    )
                    stack.append(not term_found)
                    i += 2
                else:
                    i += 1
            elif token == ')':
                i += 1
            else:
                # Regular term or phrase
                if ' ' in token:  # It's a phrase
                    found = self.phrase_search(token, doc_id)
                else:
                    found = token.lower() in self.tokenize(
                        self.documents[doc_id]['title'] + ' ' + self.documents[doc_id]['content']
                    )
                stack.append(found)
                i += 1
        
        # Final evaluation of remaining stack (default to OR)
        if not stack:
            return False
        result = stack[0]
        for val in stack[1:]:
            result = result or val
        return result
