"""
Ticker extraction module for identifying stock symbols from Reddit posts.
Uses simple exact matching against a database of valid tickers.
"""

import logging
import re
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class TickerExtractor:
    """Extracts and validates stock tickers from Reddit posts using exact matching."""
    
    def __init__(self, config: Dict):
        """Initialize extractor with configuration."""
        self.config = config
        self.valid_tickers = self._load_valid_tickers()
        self.ticker_map = self._load_ticker_map()
        
    def _load_valid_tickers(self) -> Set[str]:
        """Load valid tickers from CSV file."""
        try:
            ticker_file = Path("assets/valid_tickers.csv")
            if ticker_file.exists():
                df = pd.read_csv(ticker_file)
                # Handle empty values and ensure proper string conversion
                df['ticker'] = df['ticker'].fillna('').astype(str)
                # Filter out empty tickers and convert to uppercase
                tickers = set()
                for ticker in df['ticker'].values:
                    ticker_str = str(ticker).strip()
                    if ticker_str:
                        tickers.add(ticker_str.upper())
                logger.info(f"Loaded {len(tickers)} valid tickers from database")
                return tickers
            else:
                logger.error("valid_tickers.csv not found in assets directory")
                return set()
        except Exception as e:
            logger.error(f"Error loading valid tickers: {e}")
            return set()
    
    def _load_ticker_map(self) -> Dict[str, str]:
        """Load company name to ticker mapping."""
        try:
            ticker_file = Path("assets/ticker_map.csv")
            if ticker_file.exists():
                df = pd.read_csv(ticker_file)
                # Handle empty values and ensure proper string conversion
                df['company_name'] = df['company_name'].fillna('').astype(str)
                df['ticker'] = df['ticker'].fillna('').astype(str)
                # Filter out empty entries and create mapping
                ticker_map = {}
                for _, row in df.iterrows():
                    company_name = str(row['company_name']).strip()
                    ticker = str(row['ticker']).strip()
                    if company_name and ticker:
                        ticker_map[company_name.upper()] = ticker.upper()
                return ticker_map
            return {}
        except Exception as e:
            logger.warning(f"Could not load ticker map: {e}")
            return {}
    
    def extract_tickers(self, posts: List[Dict]) -> List[Tuple[str, float, int, List[str]]]:
        """Extract tickers from posts with weighted scoring and track source links."""
        ticker_scores = defaultdict(float)
        ticker_counts = defaultdict(int)
        ticker_links = defaultdict(list)
        
        for post in posts:
            # Ensure text fields are strings
            title = str(post.get('title', ''))
            selftext = str(post.get('selftext', ''))
            text = f"{title} {selftext}"
            
            # Ensure numeric fields are properly typed
            score = int(post.get('score', 0))
            num_comments = int(post.get('num_comments', 0))
            permalink = str(post.get('permalink', ''))
            
            # Calculate mention score
            mention_score = 1 + math.log10(score + 1) + 0.5 * math.log10(num_comments + 1)
            
            # Extract tickers from text using simple exact matching
            tickers = self._find_tickers_simple(text)
            
            for ticker in tickers:
                ticker_scores[ticker] += mention_score
                ticker_counts[ticker] += 1
                if permalink:
                    ticker_links[ticker].append(permalink)
        
        # Filter by minimum mentions and sort by score
        min_mentions = self.config['ticker_extractor']['min_mentions']
        top_n = self.config['ticker_extractor']['top_n']
        
        filtered_tickers = [
            (ticker, score, count, ticker_links[ticker]) 
            for ticker, score in ticker_scores.items()
            if (count := ticker_counts[ticker]) >= min_mentions
        ]
        
        # Sort by score descending and take top N
        filtered_tickers.sort(key=lambda x: x[1], reverse=True)
        result = filtered_tickers[:top_n]
        
        logger.info(f"Extracted {len(result)} tickers from {len(posts)} posts")
        return result
    
    def _find_tickers_simple(self, text: str) -> Set[str]:
        """Find ticker symbols using simple exact matching against the database."""
        tickers = set()
        
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
        
        # Method 1: Look for $TICKER format (most reliable)
        dollar_pattern = r'\$([A-Z]{1,5})\b'
        try:
            dollar_matches = re.findall(dollar_pattern, text)
            for match in dollar_matches:
                if match in self.valid_tickers:
                    tickers.add(match)
                    logger.debug(f"Found ticker via $ format: {match}")
        except Exception as e:
            logger.warning(f"Error in dollar pattern matching: {e}")
        
        # Method 2: Look for words that are ALL CAPS (1-5 characters)
        # This preserves the original case and finds naturally capitalized tickers
        all_caps_pattern = r'\b[A-Z]{1,5}\b'
        try:
            all_caps_matches = re.findall(all_caps_pattern, text)
            for match in all_caps_matches:
                if match in self.valid_tickers:
                    tickers.add(match)
                    logger.debug(f"Found ticker via ALL CAPS: {match}")
        except Exception as e:
            logger.warning(f"Error in ALL CAPS pattern matching: {e}")
        
        # Method 3: Check for company names in ticker_map (case-insensitive)
        # text_upper = text.upper()
        # for company_name, ticker in self.ticker_map.items():
        #     try:
        #         if company_name in text_upper and ticker in self.valid_tickers:
        #             tickers.add(ticker)
        #             logger.debug(f"Found ticker via company name '{company_name}': {ticker}")
        #     except Exception as e:
        #         logger.warning(f"Error checking company name {company_name}: {e}")
        #         continue
        
        # Log statistics
        logger.info(f"Ticker extraction stats - Text length: {len(text)}, Found tickers: {len(tickers)}, Tickers: {sorted(tickers)}")
        
        return tickers
    
    def get_ticker_details(self, ticker: str) -> Dict:
        """Get basic details for a ticker."""
        return {
            'ticker': ticker,
            'valid': ticker in self.valid_tickers
        } 