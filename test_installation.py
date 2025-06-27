#!/usr/bin/env python3
"""
Test script to verify installation and basic functionality.
"""

import sys
import importlib

def test_imports():
    """Test that all required modules can be imported."""
    required_modules = [
        'praw',
        'yfinance', 
        'pandas',
        'numpy',
        'rich',
        'yaml',
        'requests'
    ]
    
    print("Testing module imports...")
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\nFailed to import: {', '.join(failed_imports)}")
        print("Please install missing dependencies with: pip install -r requirements.txt")
        return False
    
    print("\nAll required modules imported successfully!")
    return True

def test_local_modules():
    """Test that local modules can be imported."""
    print("\nTesting local module imports...")
    
    try:
        from src.reddit_scraper import RedditScraper
        print("✓ RedditScraper")
    except ImportError as e:
        print(f"✗ RedditScraper: {e}")
        return False
    
    try:
        from src.ticker_extractor import TickerExtractor
        print("✓ TickerExtractor")
    except ImportError as e:
        print(f"✗ TickerExtractor: {e}")
        return False
    
    try:
        from src.value_analyzer import ValueAnalyzer
        print("✓ ValueAnalyzer")
    except ImportError as e:
        print(f"✗ ValueAnalyzer: {e}")
        return False
    
    try:
        from src.ranker import Ranker
        print("✓ Ranker")
    except ImportError as e:
        print(f"✗ Ranker: {e}")
        return False
    
    try:
        from src.output_writer import OutputWriter
        print("✓ OutputWriter")
    except ImportError as e:
        print(f"✗ OutputWriter: {e}")
        return False
    
    print("\nAll local modules imported successfully!")
    return True

def test_config():
    """Test that config file can be loaded."""
    print("\nTesting configuration...")
    
    try:
        import yaml
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        print("✓ config.yaml loaded successfully")
        
        # Check required sections
        required_sections = ['reddit', 'scraper', 'ticker_extractor', 'analyzer', 'ranker', 'output']
        for section in required_sections:
            if section in config:
                print(f"✓ {section} section found")
            else:
                print(f"✗ {section} section missing")
                return False
                
        return True
        
    except Exception as e:
        print(f"✗ Failed to load config.yaml: {e}")
        return False

def main():
    """Run all tests."""
    print("Value Investing Radar - Installation Test")
    print("=" * 50)
    
    success = True
    
    # Test external dependencies
    if not test_imports():
        success = False
    
    # Test local modules
    if not test_local_modules():
        success = False
    
    # Test configuration
    if not test_config():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Installation is complete.")
        print("\nNext steps:")
        print("1. Copy env.example to .env: cp env.example .env")
        print("2. Edit .env with your Reddit API credentials")
        print("3. Run: python -m src.main")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 