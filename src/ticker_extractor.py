"""
Ticker extraction module for identifying stock symbols from Reddit posts.
Includes validation against NASDAQ/NYSE tickers and weighted scoring.
"""

import logging
import re
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class TickerExtractor:
    """Extracts and validates stock tickers from Reddit posts."""
    
    def __init__(self, config: Dict):
        """Initialize extractor with configuration."""
        self.config = config
        self.valid_tickers = self._load_valid_tickers()
        self.ticker_map = self._load_ticker_map()
        
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
            
            # Extract tickers from text
            tickers = self._find_tickers(text)
            
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
    
    def _find_tickers(self, text: str) -> Set[str]:
        """Find ticker symbols in text using regex and company name mapping."""
        tickers = set()
        
        # Regex patterns for ticker symbols
        patterns = [
            r'\b[A-Z]{1,5}\b',  # Standard ticker format
            r'\$[A-Z]{1,5}\b',  # Dollar sign prefix
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.upper())
            for match in matches:
                # Clean up match
                ticker = match.replace('$', '').strip()
                if len(ticker) >= 1 and len(ticker) <= 5:
                    # Check if it's a valid ticker
                    if ticker in self.valid_tickers:
                        tickers.add(ticker)
        
        # Check for company names in ticker map
        words = text.upper().split()
        for word in words:
            if word in self.ticker_map:
                ticker = self.ticker_map[word]
                if ticker in self.valid_tickers:
                    tickers.add(ticker)
        
        return tickers
    
    def get_ticker_details(self, ticker: str) -> Dict:
        """Get basic details for a ticker."""
        return {
            'ticker': ticker,
            'valid': ticker in self.valid_tickers
        } 