"""
Unit tests for TickerExtractor module.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.ticker_extractor import TickerExtractor


class TestTickerExtractor:
    """Test cases for TickerExtractor."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = {
            'ticker_extractor': {
                'top_n': 5,
                'min_mentions': 1
            }
        }
        self.extractor = TickerExtractor(self.config)
    
    def test_load_valid_tickers_fallback(self):
        """Test loading valid tickers with fallback."""
        tickers = self.extractor.valid_tickers
        assert len(tickers) > 0
        assert 'AAPL' in tickers
        assert 'MSFT' in tickers
    
    def test_find_tickers_regex(self):
        """Test ticker extraction using regex patterns."""
        text = "I think AAPL and MSFT are great investments. Also $TSLA and GOOGL."
        tickers = self.extractor._find_tickers_smart(text)
        
        # Should find valid tickers
        assert 'AAPL' in tickers
        assert 'MSFT' in tickers
        assert 'TSLA' in tickers
        assert 'GOOGL' in tickers
    
    def test_find_tickers_invalid(self):
        """Test that invalid tickers are filtered out."""
        text = "I think INVALID and TOOLONG are not real tickers."
        tickers = self.extractor._find_tickers_smart(text)
        
        # Should not find invalid tickers
        assert 'INVALID' not in tickers
        assert 'TOOLONG' not in tickers
    
    def test_extract_tickers_with_scoring(self):
        """Test ticker extraction with popularity scoring."""
        posts = [
            {
                'title': 'AAPL is undervalued',
                'selftext': 'I think Apple is a great buy',
                'score': 100,
                'num_comments': 50
            },
            {
                'title': 'MSFT discussion',
                'selftext': 'Microsoft looks good too',
                'score': 50,
                'num_comments': 25
            },
            {
                'title': 'AAPL again',
                'selftext': 'More Apple discussion',
                'score': 75,
                'num_comments': 30
            }
        ]
        
        tickers = self.extractor.extract_tickers(posts)
        
        # Should extract tickers with scores
        assert len(tickers) > 0
        
        # AAPL should have higher score due to multiple mentions
        aapl_score = next((score for ticker, score, count, links in tickers if ticker == 'AAPL'), 0)
        msft_score = next((score for ticker, score, count, links in tickers if ticker == 'MSFT'), 0)
        
        assert aapl_score > msft_score
    
    def test_min_mentions_filter(self):
        """Test filtering by minimum mentions."""
        self.config['ticker_extractor']['min_mentions'] = 2
        
        posts = [
            {
                'title': 'AAPL mentioned once',
                'selftext': 'Apple discussion',
                'score': 100,
                'num_comments': 50
            },
            {
                'title': 'MSFT mentioned twice',
                'selftext': 'Microsoft discussion',
                'score': 50,
                'num_comments': 25
            },
            {
                'title': 'MSFT again',
                'selftext': 'More Microsoft',
                'score': 75,
                'num_comments': 30
            }
        ]
        
        tickers = self.extractor.extract_tickers(posts)
        
        # Only MSFT should appear (mentioned twice)
        ticker_symbols = [ticker for ticker, score, count, links in tickers]
        assert 'MSFT' in ticker_symbols
        assert 'AAPL' not in ticker_symbols
    
    def test_top_n_limit(self):
        """Test limiting results to top N tickers."""
        self.config['ticker_extractor']['top_n'] = 2
        
        posts = [
            {'title': 'AAPL discussion', 'selftext': 'Apple', 'score': 100, 'num_comments': 50},
            {'title': 'MSFT discussion', 'selftext': 'Microsoft', 'score': 90, 'num_comments': 45},
            {'title': 'GOOGL discussion', 'selftext': 'Google', 'score': 80, 'num_comments': 40},
            {'title': 'TSLA discussion', 'selftext': 'Tesla', 'score': 70, 'num_comments': 35}
        ]
        
        tickers = self.extractor.extract_tickers(posts)
        
        # Should only return top 2
        assert len(tickers) <= 2
    
    def test_get_ticker_details(self):
        """Test getting ticker details."""
        details = self.extractor.get_ticker_details('AAPL')
        assert details['ticker'] == 'AAPL'
        assert details['valid'] == True
        
        details = self.extractor.get_ticker_details('INVALID')
        assert details['ticker'] == 'INVALID'
        assert details['valid'] == False 