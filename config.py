import os
from dotenv import load_dotenv
from typing import Dict, Any
import json

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration manager for HypeFinder"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and config files"""
        config = {
            # Twitter API Configuration
            'twitter': {
                'api_key': os.getenv('TWITTER_API_KEY', ''),
                'api_secret': os.getenv('TWITTER_API_SECRET', ''),
                'access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
                'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET', ''),
                'bearer_token': os.getenv('TWITTER_BEARER_TOKEN', ''),
            },
            
            # Reddit API Configuration
            'reddit': {
                'client_id': os.getenv('REDDIT_CLIENT_ID', ''),
                'client_secret': os.getenv('REDDIT_CLIENT_SECRET', ''),
                'user_agent': os.getenv('REDDIT_USER_AGENT', 'HypeFinder/1.0'),
                'subreddits': ['wallstreetbets', 'cryptocurrency', 'memeeconomy', 'stockmarket']
            },
            
            # Scoring Configuration
            'scoring': {
                'volume_weight': float(os.getenv('VOLUME_WEIGHT', '0.7')),
                'sentiment_weight': float(os.getenv('SENTIMENT_WEIGHT', '0.3')),
                'top_n_tickers': int(os.getenv('TOP_N_TICKERS', '20')),
                'min_mentions': int(os.getenv('MIN_MENTIONS', '5'))
            },
            
            # Scraping Configuration
            'scraping': {
                'max_posts_per_subreddit': int(os.getenv('MAX_POSTS_PER_SUBREDDIT', '100')),
                'max_tweets': int(os.getenv('MAX_TWEETS', '100')),
                'rate_limit_delay': int(os.getenv('RATE_LIMIT_DELAY', '1')),
                'timeout': int(os.getenv('REQUEST_TIMEOUT', '30'))
            },
            
            # Output Configuration
            'output': {
                'format': os.getenv('OUTPUT_FORMAT', 'console'),  # console, csv, both
                'output_file': os.getenv('OUTPUT_FILE', 'hype_results.csv'),
                'log_level': os.getenv('LOG_LEVEL', 'INFO')
            }
        }
        
        # Load additional config from JSON file if exists
        config_file = os.getenv('CONFIG_FILE', 'config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation (e.g., 'twitter.api_key')"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def validate_api_credentials(self) -> Dict[str, bool]:
        """Validate that required API credentials are present"""
        validation = {
            'twitter': bool(self.get('twitter.bearer_token') or 
                          (self.get('twitter.api_key') and self.get('twitter.api_secret'))),
            'reddit': bool(self.get('reddit.client_id') and self.get('reddit.client_secret'))
        }
        return validation

# Global config instance
config = Config() 