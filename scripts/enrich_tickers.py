#!/usr/bin/env python3
"""
Script to enrich ticker data using SEC company tickers.
Downloads data from SEC and populates ticker_map.csv and valid_tickers.csv
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd
import requests

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SEC_LOCAL_PATH = "data/company_tickers.json"


def fetch_sec_data() -> Dict:
    """Fetch company tickers data from local file."""
    try:
        if not Path(SEC_LOCAL_PATH).exists():
            logger.error(f"Local SEC data file not found: {SEC_LOCAL_PATH}")
            return {}
        logger.info(f"Loading SEC data from {SEC_LOCAL_PATH}")
        with open(SEC_LOCAL_PATH, "r") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded {len(data)} companies from local SEC file")
        return data
    except Exception as e:
        logger.error(f"Failed to load SEC data: {e}")
        return {}


def clean_company_name(name: str) -> str:
    """Clean company name for better matching."""
    # Remove common suffixes
    suffixes = [
        ' INC', ' CORP', ' CORPORATION', ' CO', ' COMPANY', ' LLC', ' LP', ' L.P.',
        ' LTD', ' LIMITED', ' PLC', ' AG', ' SA', ' NV', ' BV', ' GROUP', ' HOLDINGS',
        ' INTERNATIONAL', ' INT\'L', ' INTL', ' TECHNOLOGIES', ' TECH', ' SYSTEMS',
        ' SOLUTIONS', ' SERVICES', ' INDUSTRIES', ' INDUSTRIAL', ' FINANCIAL',
        ' BANKING', ' INSURANCE', ' REAL ESTATE', ' PROPERTIES', ' PROPERTY'
    ]
    
    cleaned = name.upper().strip()
    
    # Remove suffixes
    for suffix in suffixes:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)].strip()
    
    # Remove extra spaces and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'[^\w\s]', '', cleaned)
    
    return cleaned.strip()


def process_sec_data(sec_data: Dict) -> tuple[List[Dict], Set[str]]:
    """Process SEC data into ticker map and valid tickers."""
    ticker_map = []
    valid_tickers = set()
    
    for company_id, company in sec_data.items():
        ticker = company.get('ticker', '').strip()
        title = company.get('title', '').strip()
        
        if not ticker or not title:
            continue
        
        # Skip if ticker is too long (likely not a valid ticker)
        if len(ticker) > 5:
            continue
        
        # Add to valid tickers
        valid_tickers.add(ticker.upper())
        
        # Create ticker map entries
        # 1. Full company name
        ticker_map.append({
            'company_name': title.upper(),
            'ticker': ticker.upper()
        })
        
        # 2. Cleaned company name
        cleaned_name = clean_company_name(title)
        if cleaned_name and cleaned_name != title.upper():
            ticker_map.append({
                'company_name': cleaned_name,
                'ticker': ticker.upper()
            })
        
        # 3. Common variations
        words = title.upper().split()
        if len(words) > 1:
            # First word (often company name)
            if len(words[0]) > 2:  # Avoid short words like "THE", "A", etc.
                ticker_map.append({
                    'company_name': words[0],
                    'ticker': ticker.upper()
                })
            
            # First two words
            if len(words) >= 2 and len(words[0]) > 2 and len(words[1]) > 2:
                ticker_map.append({
                    'company_name': f"{words[0]} {words[1]}",
                    'ticker': ticker.upper()
                })
    
    logger.info(f"Processed {len(valid_tickers)} valid tickers")
    logger.info(f"Created {len(ticker_map)} ticker map entries")
    
    return ticker_map, valid_tickers


def save_ticker_map(ticker_map: List[Dict], output_path: str):
    """Save ticker map to CSV."""
    try:
        df = pd.DataFrame(ticker_map)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['company_name', 'ticker'])
        
        # Sort by company name
        df = df.sort_values('company_name')
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} ticker map entries to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to save ticker map: {e}")


def save_valid_tickers(valid_tickers: Set[str], output_path: str):
    """Save valid tickers to CSV."""
    try:
        # Convert to list and sort
        ticker_list = sorted(list(valid_tickers))
        
        df = pd.DataFrame({
            'ticker': ticker_list,
            'company_name': [''] * len(ticker_list)  # Placeholder for company names
        })
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} valid tickers to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to save valid tickers: {e}")


def main():
    """Main function to enrich ticker data."""
    logger.info("Starting ticker data enrichment...")
    
    # Create assets directory if it doesn't exist
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    # Fetch SEC data
    sec_data = fetch_sec_data()
    if not sec_data:
        logger.error("No SEC data received. Exiting.")
        return
    
    # Process data
    ticker_map, valid_tickers = process_sec_data(sec_data)
    
    # Save files
    ticker_map_path = assets_dir / "ticker_map.csv"
    valid_tickers_path = assets_dir / "valid_tickers.csv"
    
    save_ticker_map(ticker_map, str(ticker_map_path))
    save_valid_tickers(valid_tickers, str(valid_tickers_path))
    
    # Print summary
    print("\n" + "="*60)
    print("TICKER DATA ENRICHMENT COMPLETE")
    print("="*60)
    print(f"Valid tickers: {len(valid_tickers)}")
    print(f"Ticker map entries: {len(ticker_map)}")
    print(f"Files saved:")
    print(f"  - {ticker_map_path}")
    print(f"  - {valid_tickers_path}")
    print("="*60)
    
    # Show some examples
    print("\nSample ticker map entries:")
    for i, entry in enumerate(ticker_map[:10]):
        print(f"  {entry['company_name']} -> {entry['ticker']}")
    
    print(f"\nSample valid tickers (first 20):")
    ticker_list = sorted(list(valid_tickers))
    print(f"  {', '.join(ticker_list[:20])}")


if __name__ == "__main__":
    main() 