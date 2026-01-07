import re
from collections import defaultdict


class SpellChecker:
    """Simple spell checker using edit distance and dictionary"""
    
    def __init__(self, dictionary_words):
        self.dictionary = set(word.lower() for word in dictionary_words)
        self.word_freq = defaultdict(int)
        for word in dictionary_words:
            self.word_freq[word.lower()] += 1
    
    def suggest_corrections(self, word, max_suggestions=3):
        """Suggest spelling corrections for a word"""
        word = word.lower()
        
        # If word is in dictionary, no correction needed
        if word in self.dictionary:
            return []
        
        suggestions = []
        
        # Generate candidates with edit distance 1
        candidates = self._generate_candidates(word)
        
        # Filter candidates that are in dictionary
        valid_candidates = [c for c in candidates if c in self.dictionary]
        
        # Sort by frequency (more common words first)
        valid_candidates.sort(key=lambda x: self.word_freq[x], reverse=True)
        
        return valid_candidates[:max_suggestions]
    
    def _generate_candidates(self, word):
        """Generate candidate words with edit distance 1"""
        candidates = set()
        letters = 'abcdefghijklmnopqrstuvwxyz'
        
        # Deletions
        for i in range(len(word)):
            candidates.add(word[:i] + word[i+1:])
        
        # Transpositions
        for i in range(len(word)-1):
            candidates.add(word[:i] + word[i+1] + word[i] + word[i+2:])
        
        # Substitutions
        for i in range(len(word)):
            for letter in letters:
                candidates.add(word[:i] + letter + word[i+1:])
        
        # Insertions
        for i in range(len(word)+1):
            for letter in letters:
                candidates.add(word[:i] + letter + word[i:])
        
        return candidates
    
    def correct_query(self, query):
        """Correct spelling in a query"""
        tokens = re.findall(r'\b\w+\b', query.lower())
        corrected_tokens = []
        corrections_needed = False
        
        for token in tokens:
            suggestions = self.suggest_corrections(token)
            if suggestions:
                corrected_tokens.append(suggestions[0])  # Use best suggestion
                corrections_needed = True
            else:
                corrected_tokens.append(token)
        
        corrected_query = ' '.join(corrected_tokens)
        
        # Preserve original capitalization and special characters
        if corrections_needed:
            return corrected_query, True
        else:
            return query, False
