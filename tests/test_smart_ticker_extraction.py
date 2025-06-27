#!/usr/bin/env python3
"""
Test script for the improved ticker extraction functionality.
"""

import yaml
from src.ticker_extractor import TickerExtractor

def test_smart_ticker_extraction():
    """Test the improved ticker extraction with various scenarios."""
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize ticker extractor
    extractor = TickerExtractor(config)
    
    # Test cases with different scenarios
    test_posts = [
        {
            'title': 'What do you think about $AAPL at current levels?',
            'selftext': 'Apple looks undervalued to me. I think it\'s a good buy.',
            'score': 10,
            'num_comments': 5
        },
        {
            'title': 'SEE this stock analysis',
            'selftext': 'I SEE potential in this company. CASH flow looks good.',
            'score': 5,
            'num_comments': 2
        },
        {
            'title': 'MSFT and GOOGL comparison',
            'selftext': 'Microsoft stock is trading at $300 while Google is at $150. Both look good.',
            'score': 15,
            'num_comments': 8
        },
        {
            'title': 'WELL Health Technologies analysis',
            'selftext': 'WELL is a healthcare stock that I\'m considering. NEXT earnings should be good.',
            'score': 8,
            'num_comments': 3
        },
        {
            'title': 'REAL estate stocks: LOW and HD',
            'selftext': 'Lowe\'s and Home Depot are both good real estate plays. LOW is cheaper.',
            'score': 12,
            'num_comments': 6
        },
        {
            'title': 'Buy TSLA or wait?',
            'selftext': 'Tesla stock is volatile but I think it\'s worth buying at these levels.',
            'score': 20,
            'num_comments': 15
        }
    ]
    
    print("Testing Smart Ticker Extraction")
    print("=" * 50)
    
    # Extract tickers
    results = extractor.extract_tickers(test_posts)
    
    print(f"\nExtracted {len(results)} tickers:")
    for ticker, score, count in results:
        print(f"  {ticker}: score={score:.2f}, mentions={count}")
    
    # Test individual text processing
    print("\n" + "=" * 50)
    print("Testing individual text processing:")
    
    test_texts = [
        "I think $AAPL is a good buy at $150",
        "SEE this analysis of CASH flow",
        "MSFT stock looks undervalued",
        "WELL Health is a good company",
        "LOW and HD are both good",
        "REAL estate stocks like LOW"
    ]
    
    for text in test_texts:
        tickers = extractor._find_tickers_smart(text)
        print(f"\nText: '{text}'")
        print(f"Found tickers: {list(tickers)}")
    
    # Test validation
    print("\n" + "=" * 50)
    print("Testing ticker validation:")
    
    test_tickers = ['AAPL', 'SEE', 'CASH', 'WELL', 'LOW', 'REAL', 'MSFT', 'GOOGL', 'TSLA']
    
    for ticker in test_tickers:
        is_valid = extractor._is_valid_ticker(ticker)
        print(f"  {ticker}: {'VALID' if is_valid else 'INVALID'}")

if __name__ == "__main__":
    test_smart_ticker_extraction() 