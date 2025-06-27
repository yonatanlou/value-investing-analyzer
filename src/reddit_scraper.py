"""
Reddit scraper module for fetching posts from r/ValueInvesting.
Supports PRAW with Pushshift fallback for rate limiting.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import praw
import requests
from praw.models import Submission

logger = logging.getLogger(__name__)


class RedditScraper:
    """Scrapes Reddit posts from r/ValueInvesting subreddit."""
    
    def __init__(self, config: Dict):
        """Initialize scraper with configuration."""
        self.config = config
        self.reddit = None
        self._init_praw()
        
    def _init_praw(self) -> None:
        """Initialize PRAW client if credentials are provided."""
        reddit_config = self.config.get('reddit', {})
        client_id = reddit_config.get('client_id')
        client_secret = reddit_config.get('client_secret')
        user_agent = reddit_config.get('user_agent')
        
        if client_id != "REPLACE_ME" and client_secret != "REPLACE_ME":
            try:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                logger.info("PRAW client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize PRAW: {e}")
                self.reddit = None
        else:
            logger.info("Using Pushshift fallback (no PRAW credentials)")
    
    def scrape_posts(self) -> List[Dict]:
        """Scrape posts from r/ValueInvesting for the specified time period."""
        if self.reddit:
            return self._scrape_with_praw()
        else:
            return self._scrape_with_pushshift()
    
    def _scrape_with_praw(self) -> List[Dict]:
        """Scrape using PRAW API."""
        subreddit_name = self.config['scraper']['subreddit']
        days_back = self.config['scraper']['days_back']
        max_posts = self.config['scraper']['max_posts']
        
        cutoff_time = datetime.now() - timedelta(days=days_back)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        posts = []
        subreddit = self.reddit.subreddit(subreddit_name)
        
        try:
            for submission in subreddit.new(limit=max_posts):
                if submission.created_utc < cutoff_timestamp:
                    break
                    
                post_data = {
                    'title': submission.title,
                    'selftext': submission.selftext,
                    'score': submission.score,
                    'num_comments': submission.num_comments,
                    'created_utc': submission.created_utc,
                    'permalink': submission.permalink,
                    'id': submission.id
                }
                posts.append(post_data)
                
                # Rate limiting
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error scraping with PRAW: {e}")
            return []
            
        logger.info(f"Scraped {len(posts)} posts with PRAW")
        return posts
    
    def _scrape_with_pushshift(self) -> List[Dict]:
        """Scrape using Pushshift API as fallback."""
        subreddit_name = self.config['scraper']['subreddit']
        days_back = self.config['scraper']['days_back']
        max_posts = self.config['scraper']['max_posts']
        
        cutoff_time = datetime.now() - timedelta(days=days_back)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        url = "https://api.pushshift.io/reddit/search/submission/"
        params = {
            'subreddit': subreddit_name,
            'after': cutoff_timestamp,
            'size': max_posts,
            'sort': 'desc',
            'sort_type': 'created_utc'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            for post in data.get('data', []):
                post_data = {
                    'title': post.get('title', ''),
                    'selftext': post.get('selftext', ''),
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_utc': post.get('created_utc', 0),
                    'permalink': f"https://reddit.com{post.get('permalink', '')}",
                    'id': post.get('id', '')
                }
                posts.append(post_data)
                
        except Exception as e:
            logger.error(f"Error scraping with Pushshift: {e}")
            return []
            
        logger.info(f"Scraped {len(posts)} posts with Pushshift")
        return posts
    
    def save_raw_data(self, posts: List[Dict]) -> None:
        """Save raw scraped data to JSON file for auditability."""
        if not posts:
            return
            
        data_dir = Path("data/raw")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = data_dir / f"{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(posts, f, indent=2)
            
        logger.info(f"Saved raw data to {filename}") 