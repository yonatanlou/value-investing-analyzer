"""
Main CLI entry point for the Value Investing Radar.
Orchestrates the entire analysis pipeline from Reddit scraping to output generation.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict

import yaml
from dotenv import load_dotenv

from .reddit_scraper import RedditScraper
from .ticker_extractor import TickerExtractor
from .value_analyzer import ValueAnalyzer
from .ranker import Ranker
from .output_writer import OutputWriter


def setup_logging(config: Dict) -> None:
    """Setup logging configuration."""
    log_level = config.get('logging', {}).get('level', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file with environment variable substitution."""
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Replace environment variables
        config_content = os.path.expandvars(config_content)
        
        config = yaml.safe_load(config_content)
        return config
    except Exception as e:
        print(f"Error loading config file {config_path}: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Value Investing Radar - Analyze Reddit value investing discussions"
    )
    parser.add_argument(
        '--config', 
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without saving output files'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Value Investing Radar analysis")
    
    try:
        # Step 1: Scrape Reddit posts
        logger.info("Step 1: Scraping Reddit posts...")
        scraper = RedditScraper(config)
        posts = scraper.scrape_posts()
        
        if not posts:
            logger.error("No posts scraped. Exiting.")
            sys.exit(1)
        
        logger.info(f"Scraped {len(posts)} posts")
        
        # Save raw data for auditability
        if not args.dry_run:
            scraper.save_raw_data(posts)
        
        # Step 2: Extract tickers
        logger.info("Step 2: Extracting tickers...")
        extractor = TickerExtractor(config)
        tickers = extractor.extract_tickers(posts)
        
        if not tickers:
            logger.error("No tickers extracted. Exiting.")
            sys.exit(1)
        
        logger.info(f"Extracted {len(tickers)} tickers")
        
        # Step 3: Analyze fundamentals
        logger.info("Step 3: Analyzing fundamentals...")
        analyzer = ValueAnalyzer(config)
        analyzed_stocks = analyzer.analyze_tickers(tickers)
        
        if not analyzed_stocks:
            logger.error("No stocks analyzed. Exiting.")
            sys.exit(1)
        
        logger.info(f"Analyzed {len(analyzed_stocks)} stocks")
        
        # Step 4: Rank and recommend
        logger.info("Step 4: Ranking stocks...")
        ranker = Ranker(config)
        ranked_stocks = ranker.rank_stocks(analyzed_stocks)
        
        if not ranked_stocks:
            logger.error("No stocks ranked. Exiting.")
            sys.exit(1)
        
        # Get summary statistics
        summary_stats = ranker.get_summary_stats(ranked_stocks)
        
        # Step 5: Generate output
        logger.info("Step 5: Generating output...")
        output_writer = OutputWriter(config)
        output_writer.write_output(ranked_stocks, summary_stats)
        
        logger.info("Analysis completed successfully!")
        
        # Print final summary
        print(f"\n{'='*60}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Posts analyzed: {len(posts)}")
        print(f"Tickers found: {len(tickers)}")
        print(f"Stocks analyzed: {len(analyzed_stocks)}")
        print(f"BUY recommendations: {summary_stats.get('buy_count', 0)}")
        print(f"HOLD recommendations: {summary_stats.get('hold_count', 0)}")
        print(f"AVOID recommendations: {summary_stats.get('avoid_count', 0)}")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 