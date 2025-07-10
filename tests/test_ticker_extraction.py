#!/usr/bin/env python3
"""
Test script to show ticker extraction with different settings.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

from src.ticker_extractor import TickerExtractor

def test_ticker_extraction():
    """Test ticker extraction with different settings."""
    
    # Load existing data
    data_file = Path("data/raw/2025-06-27.json")
    if not data_file.exists():
        print("No existing data found. Run the main script first.")
        return
    
    with open(data_file, 'r') as f:
        posts = json.load(f)
    
    print(f"Loaded {len(posts)} posts from existing data")
    
    # Test different configurations
    configs = [
        {"top_n": 15, "min_mentions": 2, "name": "Current (15 stocks, min 2 mentions)"},
        {"top_n": 30, "min_mentions": 1, "name": "More stocks (30 stocks, min 1 mention)"},
        {"top_n": 50, "min_mentions": 1, "name": "Many stocks (50 stocks, min 1 mention)"},
    ]
    
    for config in configs:
        print(f"\n{'='*60}")
        print(f"Testing: {config['name']}")
        print(f"{'='*60}")
        
        # Create test config
        test_config = {
            'ticker_extractor': {
                'top_n': config['top_n'],
                'min_mentions': config['min_mentions']
            }
        }
        
        # Extract tickers
        extractor = TickerExtractor(test_config)
        tickers = extractor.extract_tickers(posts)
        
        print(f"Found {len(tickers)} tickers")
        print(f"Top 10 tickers:")
        for i, (ticker, score, count, links) in enumerate(tickers[:10], 1):
            print(f"  {i:2d}. {ticker:6s} (score: {score:6.1f}, mentions: {count}, links: {len(links)})")
        
        if len(tickers) > 10:
            print(f"  ... and {len(tickers) - 10} more")

if __name__ == "__main__":
    test_ticker_extraction() 