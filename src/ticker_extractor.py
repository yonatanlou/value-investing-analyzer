"""
Ticker extraction module for identifying stock symbols from Reddit posts.
Uses NLTK for Named Entity Recognition and POS tagging to avoid common words.
"""

import logging
import re
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pandas as pd
import requests
import nltk
from nltk import pos_tag, word_tokenize
from nltk.chunk import ne_chunk

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')
try:
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    nltk.download('averaged_perceptron_tagger_eng')
try:
    nltk.data.find('chunkers/maxent_ne_chunker')
except LookupError:
    nltk.download('maxent_ne_chunker')
try:
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('words')


class TickerExtractor:
    """Extracts and validates stock tickers from Reddit posts using NLTK."""
    
    def __init__(self, config: Dict):
        """Initialize extractor with configuration."""
        self.config = config
        self.valid_tickers = self._load_valid_tickers()
        self.ticker_map = self._load_ticker_map()
        self.common_words = self._load_common_words()
        
    def _load_valid_tickers(self) -> Set[str]:
        """Load valid tickers from NASDAQ/NYSE or use fallback list."""
        try:
            # Try to load from assets directory first
            ticker_file = Path("assets/valid_tickers.csv")
            if ticker_file.exists():
                df = pd.read_csv(ticker_file)
                return set(df['ticker'].str.upper().tolist())
            
            # Fallback: common large-cap tickers
            fallback_tickers = {
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK.B',
                'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'PFE', 'ABBV', 'KO', 'PEP',
                'AVGO', 'COST', 'TMO', 'DHR', 'ACN', 'NEE', 'LLY', 'ABT', 'TXN',
                'VZ', 'CMCSA', 'ADBE', 'CRM', 'NFLX', 'PYPL', 'INTC', 'QCOM',
                'AMD', 'INTU', 'HON', 'AMGN', 'IBM', 'T', 'ORCL', 'CSCO', 'GE',
                'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'AXP',
                'SPY', 'QQQ', 'VTI', 'VOO', 'IVV', 'DIA', 'IWM', 'VEA', 'VWO'
            }
            logger.info(f"Using fallback ticker list with {len(fallback_tickers)} tickers")
            return fallback_tickers
            
        except Exception as e:
            logger.error(f"Error loading valid tickers: {e}")
            return set()
    
    def _load_ticker_map(self) -> Dict[str, str]:
        """Load company name to ticker mapping."""
        try:
            ticker_file = Path("assets/ticker_map.csv")
            if ticker_file.exists():
                df = pd.read_csv(ticker_file)
                return dict(zip(df['company_name'].str.upper(), df['ticker'].str.upper()))
            return {}
        except Exception as e:
            logger.warning(f"Could not load ticker map: {e}")
            return {}
    
    def _load_common_words(self) -> Set[str]:
        """Load common English words to filter out."""
        try:
            # Use NLTK's word list
            from nltk.corpus import words
            common_words = set(words.words())
            
            # Add common short words that are often mistaken for tickers
            short_common_words = {
                'A', 'I', 'AN', 'AS', 'AT', 'BE', 'BY', 'DO', 'GO', 'HE', 'IF', 'IN', 'IS', 'IT', 'ME', 'MY', 'NO', 'OF', 'ON', 'OR', 'SO', 'TO', 'UP', 'US', 'WE',
                'ALL', 'AND', 'ANY', 'ARE', 'BAD', 'BIG', 'BUT', 'CAN', 'DID', 'END', 'FOR', 'GET', 'HAD', 'HAS', 'HER', 'HIM', 'HIS', 'HOW', 'ITS', 'LET', 'LOW', 'MAN', 'MAY', 'NEW', 'NOT', 'NOW', 'OLD', 'ONE', 'OUR', 'OUT', 'OWN', 'SAY', 'SEE', 'SHE', 'THE', 'TOO', 'TRY', 'TWO', 'USE', 'WAY', 'WHO', 'WHY', 'YES', 'YOU',
                'ABOUT', 'AFTER', 'AGAIN', 'ALSO', 'ANOTHER', 'BEFORE', 'BEING', 'BELOW', 'BETWEEN', 'CALLED', 'CAME', 'COME', 'COULD', 'EACH', 'EVEN', 'FIRST', 'FOUND', 'FROM', 'GIVE', 'GIVE', 'GOOD', 'HERE', 'HIGH', 'INTO', 'JUST', 'KNOW', 'LAST', 'LEFT', 'LIFE', 'LONG', 'LOOK', 'MADE', 'MAKE', 'MOST', 'MOVE', 'MUST', 'NAME', 'NEED', 'NEXT', 'ONLY', 'OVER', 'PART', 'PEOPLE', 'PLACE', 'REAL', 'RIGHT', 'SAID', 'SAME', 'SHOULD', 'SOME', 'STILL', 'SUCH', 'TAKE', 'THAN', 'THAT', 'THEIR', 'THEM', 'THEN', 'THERE', 'THESE', 'THEY', 'THING', 'THINK', 'THIS', 'THOSE', 'THROUGH', 'TIME', 'UNDER', 'VERY', 'WANT', 'WAS', 'WELL', 'WENT', 'WERE', 'WHAT', 'WHEN', 'WHERE', 'WHICH', 'WHILE', 'WILL', 'WITH', 'WORK', 'YEAR', 'YOUR'
            }
            
            # Combine and convert to uppercase
            all_common_words = common_words.union(short_common_words)
            return {word.upper() for word in all_common_words if len(word) <= 5}
            
        except Exception as e:
            logger.warning(f"Could not load common words: {e}")
            # Fallback to basic common words
            return {
                'A', 'I', 'AN', 'AS', 'AT', 'BE', 'BY', 'DO', 'GO', 'HE', 'IF', 'IN', 'IS', 'IT', 'ME', 'MY', 'NO', 'OF', 'ON', 'OR', 'SO', 'TO', 'UP', 'US', 'WE',
                'ALL', 'AND', 'ANY', 'ARE', 'BAD', 'BIG', 'BUT', 'CAN', 'DID', 'END', 'FOR', 'GET', 'HAD', 'HAS', 'HER', 'HIM', 'HIS', 'HOW', 'ITS', 'LET', 'LOW', 'MAN', 'MAY', 'NEW', 'NOT', 'NOW', 'OLD', 'ONE', 'OUR', 'OUT', 'OWN', 'SAY', 'SEE', 'SHE', 'THE', 'TOO', 'TRY', 'TWO', 'USE', 'WAY', 'WHO', 'WHY', 'YES', 'YOU'
            }
    
    def extract_tickers(self, posts: List[Dict]) -> List[Tuple[str, float, int]]:
        """Extract tickers from posts with weighted scoring."""
        ticker_scores = defaultdict(float)
        ticker_counts = defaultdict(int)
        
        for post in posts:
            text = f"{post['title']} {post['selftext']}"
            score = post.get('score', 0)
            num_comments = post.get('num_comments', 0)
            
            # Calculate mention score
            mention_score = 1 + math.log10(score + 1) + 0.5 * math.log10(num_comments + 1)
            
            # Extract tickers from text using improved method
            tickers = self._find_tickers_smart(text)
            
            for ticker in tickers:
                ticker_scores[ticker] += mention_score
                ticker_counts[ticker] += 1
        
        # Filter by minimum mentions and sort by score
        min_mentions = self.config['ticker_extractor']['min_mentions']
        top_n = self.config['ticker_extractor']['top_n']
        
        filtered_tickers = [
            (ticker, score, count) 
            for ticker, score in ticker_scores.items()
            if (count := ticker_counts[ticker]) >= min_mentions
        ]
        
        # Sort by score descending and take top N
        filtered_tickers.sort(key=lambda x: x[1], reverse=True)
        result = filtered_tickers[:top_n]
        
        logger.info(f"Extracted {len(result)} tickers from {len(posts)} posts")
        return result
    
    def _find_tickers_smart(self, text: str) -> Set[str]:
        """Find ticker symbols using NLTK and smart heuristics."""
        tickers = set()
        
        # Convert to uppercase for consistency
        text_upper = text.upper()
        
        # Method 1: Look for ticker patterns with context
        ticker_patterns = self._find_ticker_patterns(text_upper)
        tickers.update(ticker_patterns)
        
        # Method 2: Use NLTK NER to find company names
        ner_tickers = self._find_tickers_with_ner(text)
        tickers.update(ner_tickers)
        
        # Method 3: Check company name mappings
        company_tickers = self._find_tickers_from_company_names(text_upper)
        tickers.update(company_tickers)
        
        # Filter out common words and validate
        filtered_tickers = set()
        for ticker in tickers:
            if self._is_valid_ticker(ticker):
                filtered_tickers.add(ticker)
        
        return filtered_tickers
    
    def _find_ticker_patterns(self, text: str) -> Set[str]:
        """Find ticker patterns with better context awareness."""
        tickers = set()
        
        # Pattern 1: $TICKER format (most reliable)
        dollar_pattern = r'\$([A-Z]{1,5})\b'
        dollar_matches = re.findall(dollar_pattern, text)
        for match in dollar_matches:
            tickers.add(match)
        
        # Pattern 2: TICKER in investment context (more specific)
        # Look for patterns like "buy TICKER", "TICKER stock", "invest in TICKER"
        investment_patterns = [
            r'\b(BUY|INVEST|HOLD|SELL|SHORT|LONG)\s+([A-Z]{1,5})\b',
            r'\b([A-Z]{1,5})\s+(STOCK|SHARES?|EQUITY|POSITION)\b',
            r'\b(INVEST\s+IN|BUY\s+INTO)\s+([A-Z]{1,5})\b',
            r'\b([A-Z]{1,5})\s+(IS\s+UNDERVALUED|IS\s+OVERVALUED|LOOKS\s+GOOD|IS\s+A\s+BUY)\b',
            r'\b([A-Z]{1,5})\s+(TECHNOLOGIES|CORPORATION|COMPANY|INC|LTD|LLC)\b',
            r'\b([A-Z]{1,5})\s+(ANALYSIS|REVIEW|DD|DUE\s+DILIGENCE)\b'
        ]
        
        for pattern in investment_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # Extract the ticker from the tuple
                    for group in match:
                        if len(group) >= 1 and len(group) <= 5 and group.isalpha():
                            tickers.add(group)
                else:
                    if len(match) >= 1 and len(match) <= 5 and match.isalpha():
                        tickers.add(match)
        
        # Pattern 3: TICKER in price context (more specific)
        price_patterns = [
            r'\b([A-Z]{1,5})\s+(\$?\d+\.?\d*)\b',  # TICKER $50.00
            r'\b(\$?\d+\.?\d*)\s+([A-Z]{1,5})\b',  # $50.00 TICKER
            r'\b([A-Z]{1,5})\s+(AT|TRADING\s+AT)\s+\$?\d+\.?\d*\b',  # TICKER at $50
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    for group in match:
                        if len(group) >= 1 and len(group) <= 5 and group.isalpha():
                            tickers.add(group)
        
        return tickers
    
    def _find_tickers_with_ner(self, text: str) -> Set[str]:
        """Use NLTK Named Entity Recognition to find company names."""
        tickers = set()
        
        try:
            # Tokenize and tag parts of speech
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            # Extract named entities
            named_entities = ne_chunk(pos_tags)
            
            # Look for ORGANIZATION entities
            for chunk in named_entities:
                if hasattr(chunk, 'label') and chunk.label() == 'ORGANIZATION':
                    org_name = ' '.join([token for token, pos in chunk.leaves()])
                    org_upper = org_name.upper()
                    
                    # Check if this organization name maps to a ticker
                    if org_upper in self.ticker_map:
                        ticker = self.ticker_map[org_upper]
                        if ticker in self.valid_tickers:
                            tickers.add(ticker)
                    
                    # Also check individual words in the organization name
                    for word in org_upper.split():
                        if word in self.ticker_map:
                            ticker = self.ticker_map[word]
                            if ticker in self.valid_tickers:
                                tickers.add(ticker)
                                
        except Exception as e:
            logger.warning(f"Error in NER processing: {e}")
        
        return tickers
    
    def _find_tickers_from_company_names(self, text: str) -> Set[str]:
        """Find tickers by matching company names in the text."""
        tickers = set()
        
        # Check for exact company name matches
        for company_name, ticker in self.ticker_map.items():
            if company_name in text:
                if ticker in self.valid_tickers:
                    tickers.add(ticker)
        
        # Check for partial matches (first word of company name)
        words = text.split()
        for word in words:
            if word in self.ticker_map:
                ticker = self.ticker_map[word]
                if ticker in self.valid_tickers:
                    tickers.add(ticker)
        
        return tickers
    
    def _is_valid_ticker(self, ticker: str) -> bool:
        """Validate if a potential ticker is actually a valid stock ticker."""
        # Must be in valid tickers list
        if ticker not in self.valid_tickers:
            return False
        
        # Must not be a common English word
        if ticker in self.common_words:
            return False
        
        # Must be 1-5 characters
        if len(ticker) < 1 or len(ticker) > 5:
            return False
        
        # Must be all uppercase letters
        if not ticker.isalpha() or not ticker.isupper():
            return False
        
        # Additional checks for common false positives
        common_false_positives = {
            'A', 'I', 'AN', 'AS', 'AT', 'BE', 'BY', 'DO', 'GO', 'HE', 'IF', 'IN', 'IS', 'IT', 'ME', 'MY', 'NO', 'OF', 'ON', 'OR', 'SO', 'TO', 'UP', 'US', 'WE',
            'ALL', 'AND', 'ANY', 'ARE', 'BAD', 'BIG', 'BUT', 'CAN', 'DID', 'END', 'FOR', 'GET', 'HAD', 'HAS', 'HER', 'HIM', 'HIS', 'HOW', 'ITS', 'LET', 'LOW', 'MAN', 'MAY', 'NEW', 'NOT', 'NOW', 'OLD', 'ONE', 'OUR', 'OUT', 'OWN', 'SAY', 'SEE', 'SHE', 'THE', 'TOO', 'TRY', 'TWO', 'USE', 'WAY', 'WHO', 'WHY', 'YES', 'YOU',
            'ABOUT', 'AFTER', 'AGAIN', 'ALSO', 'ANOTHER', 'BEFORE', 'BEING', 'BELOW', 'BETWEEN', 'CALLED', 'CAME', 'COME', 'COULD', 'EACH', 'EVEN', 'FIRST', 'FOUND', 'FROM', 'GIVE', 'GIVE', 'GOOD', 'HERE', 'HIGH', 'INTO', 'JUST', 'KNOW', 'LAST', 'LEFT', 'LIFE', 'LONG', 'LOOK', 'MADE', 'MAKE', 'MOST', 'MOVE', 'MUST', 'NAME', 'NEED', 'NEXT', 'ONLY', 'OVER', 'PART', 'PEOPLE', 'PLACE', 'REAL', 'RIGHT', 'SAID', 'SAME', 'SHOULD', 'SOME', 'STILL', 'SUCH', 'TAKE', 'THAN', 'THAT', 'THEIR', 'THEM', 'THEN', 'THERE', 'THESE', 'THEY', 'THING', 'THINK', 'THIS', 'THOSE', 'THROUGH', 'TIME', 'UNDER', 'VERY', 'WANT', 'WAS', 'WELL', 'WENT', 'WERE', 'WHAT', 'WHEN', 'WHERE', 'WHICH', 'WHILE', 'WILL', 'WITH', 'WORK', 'YEAR', 'YOUR',
            'CASH', 'COST', 'DEBT', 'EARN', 'FACE', 'FALL', 'FARM', 'FEEL', 'FILL', 'FIND', 'FINE', 'FIRE', 'FISH', 'FIVE', 'FOLD', 'FOOD', 'FOOT', 'FORM', 'FOUR', 'FREE', 'FROM', 'FULL', 'GAME', 'GAVE', 'GIVE', 'GOLD', 'GONE', 'GOOD', 'GOT', 'HALF', 'HAND', 'HARD', 'HAVE', 'HEAD', 'HEAR', 'HELP', 'HERE', 'HIGH', 'HOLD', 'HOME', 'HOPE', 'HOUR', 'IDEA', 'INTO', 'ITEM', 'JUST', 'KEEP', 'KIND', 'KNOW', 'LAND', 'LAST', 'LATE', 'LEFT', 'LESS', 'LIFE', 'LIFT', 'LIKE', 'LINE', 'LIVE', 'LONG', 'LOOK', 'LOST', 'LOTS', 'LOVE', 'MADE', 'MAIN', 'MAKE', 'MANY', 'MEAN', 'MIND', 'MISS', 'MORE', 'MOST', 'MOVE', 'MUCH', 'MUST', 'NAME', 'NEAR', 'NEED', 'NEXT', 'NINE', 'ONCE', 'ONLY', 'OPEN', 'OVER', 'PART', 'PASS', 'PAST', 'PICK', 'PLAN', 'PLAY', 'POOR', 'PULL', 'PUSH', 'PUT', 'READ', 'REAL', 'REST', 'RIDE', 'ROAD', 'ROCK', 'ROOM', 'RULE', 'SAFE', 'SAID', 'SAME', 'SAVE', 'SEEM', 'SEND', 'SHOW', 'SIDE', 'SIGN', 'SING', 'SITE', 'SIZE', 'SLOW', 'SOON', 'STOP', 'SURE', 'TAKE', 'TALK', 'TEAM', 'TELL', 'TEST', 'THAN', 'THAT', 'THEM', 'THEN', 'THEY', 'THIS', 'TIME', 'TOLD', 'TOOK', 'TOWN', 'TURN', 'TYPE', 'UNDER', 'USED', 'VERY', 'WALK', 'WANT', 'WARM', 'WAS', 'WEEK', 'WELL', 'WENT', 'WERE', 'WHAT', 'WHEN', 'WHERE', 'WHICH', 'WHILE', 'WILL', 'WITH', 'WORD', 'WORK', 'YEAR'
        }
        
        if ticker in common_false_positives:
            return False
        
        # Additional heuristic: if it's a 3-letter word, be more strict
        if len(ticker) == 3:
            # Common 3-letter words that are often false positives
            three_letter_false_positives = {
                'ALL', 'AND', 'ANY', 'ARE', 'BAD', 'BIG', 'BUT', 'CAN', 'DID', 'END', 'FOR', 'GET', 'HAD', 'HAS', 'HER', 'HIM', 'HIS', 'HOW', 'ITS', 'LET', 'LOW', 'MAN', 'MAY', 'NEW', 'NOT', 'NOW', 'OLD', 'ONE', 'OUR', 'OUT', 'OWN', 'SAY', 'SEE', 'SHE', 'THE', 'TOO', 'TRY', 'TWO', 'USE', 'WAY', 'WHO', 'WHY', 'YES', 'YOU',
                'CASH', 'COST', 'DEBT', 'EARN', 'FACE', 'FALL', 'FARM', 'FEEL', 'FILL', 'FIND', 'FINE', 'FIRE', 'FISH', 'FIVE', 'FOLD', 'FOOD', 'FOOT', 'FORM', 'FOUR', 'FREE', 'FROM', 'FULL', 'GAME', 'GAVE', 'GIVE', 'GOLD', 'GONE', 'GOOD', 'GOT', 'HALF', 'HAND', 'HARD', 'HAVE', 'HEAD', 'HEAR', 'HELP', 'HERE', 'HIGH', 'HOLD', 'HOME', 'HOPE', 'HOUR', 'IDEA', 'INTO', 'ITEM', 'JUST', 'KEEP', 'KIND', 'KNOW', 'LAND', 'LAST', 'LATE', 'LEFT', 'LESS', 'LIFE', 'LIFT', 'LIKE', 'LINE', 'LIVE', 'LONG', 'LOOK', 'LOST', 'LOTS', 'LOVE', 'MADE', 'MAIN', 'MAKE', 'MANY', 'MEAN', 'MIND', 'MISS', 'MORE', 'MOST', 'MOVE', 'MUCH', 'MUST', 'NAME', 'NEAR', 'NEED', 'NEXT', 'NINE', 'ONCE', 'ONLY', 'OPEN', 'OVER', 'PART', 'PASS', 'PAST', 'PICK', 'PLAN', 'PLAY', 'POOR', 'PULL', 'PUSH', 'PUT', 'READ', 'REAL', 'REST', 'RIDE', 'ROAD', 'ROCK', 'ROOM', 'RULE', 'SAFE', 'SAID', 'SAME', 'SAVE', 'SEEM', 'SEND', 'SHOW', 'SIDE', 'SIGN', 'SING', 'SITE', 'SIZE', 'SLOW', 'SOON', 'STOP', 'SURE', 'TAKE', 'TALK', 'TEAM', 'TELL', 'TEST', 'THAN', 'THAT', 'THEM', 'THEN', 'THEY', 'THIS', 'TIME', 'TOLD', 'TOOK', 'TOWN', 'TURN', 'TYPE', 'UNDER', 'USED', 'VERY', 'WALK', 'WANT', 'WARM', 'WAS', 'WEEK', 'WELL', 'WENT', 'WERE', 'WHAT', 'WHEN', 'WHERE', 'WHICH', 'WHILE', 'WILL', 'WITH', 'WORD', 'WORK', 'YEAR'
            }
            if ticker in three_letter_false_positives:
                return False
        
        return True
    
    def get_ticker_details(self, ticker: str) -> Dict:
        """Get basic details for a ticker."""
        return {
            'ticker': ticker,
            'valid': ticker in self.valid_tickers
        } 