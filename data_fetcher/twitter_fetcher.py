import tweepy
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base_fetcher import BaseFetcher

class TwitterFetcher(BaseFetcher):
    """Fetches trending tweets related to stocks and crypto"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_client = self._setup_twitter_client()
        
        # Search terms for finding relevant tweets
        self.search_terms = [
            "$",  # Ticker symbol prefix
            "stock",
            "crypto", 
            "moon",
            "bullish",
            "bearish",
            "buy",
            "sell",
            "pump",
            "dump",
            "hodl",
            "diamond hands",
            "paper hands",
            "to the moon",
            "rocket",
            "stonks"
        ]
    
    def _setup_twitter_client(self) -> Optional[tweepy.Client]:
        """Initialize Twitter API client"""
        try:
            bearer_token = self.config.get('bearer_token')
            
            if not bearer_token:
                # Fallback to API key/secret if no bearer token
                api_key = self.config.get('api_key')
                api_secret = self.config.get('api_secret')
                access_token = self.config.get('access_token')
                access_token_secret = self.config.get('access_token_secret')
                
                if not all([api_key, api_secret, access_token, access_token_secret]):
                    self.logger.error("Missing Twitter API credentials")
                    return None
                
                client = tweepy.Client(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret
                )
            else:
                client = tweepy.Client(bearer_token=bearer_token)
            
            # Return client without testing to avoid rate limits
            if bearer_token:
                self.logger.info("Twitter API client initialized (Bearer Token)")
            else:
                self.logger.info("Twitter API client initialized (OAuth 1.0a)")
            return client
                
        except Exception as e:
            self.logger.error(f"Failed to setup Twitter client: {e}")
            return None
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch tweets using search terms"""
        if not self.api_client:
            self.logger.error("Twitter client not available")
            return []
        
        all_tweets = []
        max_tweets = self.config.get('max_tweets', 100)
        tweets_per_query = min(100, max_tweets)  # Twitter API limit
        
        # Search for tweets with financial keywords
        query_parts = []
        
        # Add ticker symbol search
        query_parts.append("$")
        
        # Add keyword searches
        finance_keywords = ["stock market", "crypto", "trading", "bullish", "bearish"]
        query_parts.extend(finance_keywords)
        
        # Combine with OR operators
        query = " OR ".join([f'"{term}"' for term in query_parts])
        query += " -is:retweet lang:en"  # Exclude retweets, English only
        
        try:
            self.logger.info(f"Searching Twitter with query: {query}")
            
            # Search recent tweets
            tweets = tweepy.Paginator(
                self.api_client.search_recent_tweets,
                query=query,
                max_results=tweets_per_query,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations']
            ).flatten(limit=max_tweets)
            
            for tweet in tweets:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'author_id': tweet.author_id,
                    'metrics': tweet.public_metrics if hasattr(tweet, 'public_metrics') else {},
                    'source': 'twitter'
                }
                all_tweets.append(tweet_data)
                
            self.logger.info(f"Fetched {len(all_tweets)} tweets")
            return all_tweets
            
        except tweepy.TooManyRequests:
            self.logger.warning("Twitter rate limit exceeded")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching Twitter data: {e}")
            return []
    
    def fetch_trending_topics(self) -> List[str]:
        """Fetch trending topics if available"""
        if not self.api_client:
            return []
        
        try:
            # This requires higher API access level
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.debug(f"Could not fetch trending topics: {e}")
            return []
    
    def parse_posts(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse Twitter data into standardized format"""
        parsed_posts = []
        
        for tweet_data in raw_data:
            try:
                # Clean text content
                text = self.clean_text(tweet_data.get('text', ''))
                
                if not text:
                    continue
                
                # Extract metrics
                metrics = tweet_data.get('metrics', {})
                engagement = (
                    metrics.get('retweet_count', 0) + 
                    metrics.get('like_count', 0) + 
                    metrics.get('reply_count', 0)
                )
                
                parsed_post = {
                    'id': str(tweet_data.get('id', '')),
                    'text': text,
                    'source': 'twitter',
                    'timestamp': tweet_data.get('created_at'),
                    'author': tweet_data.get('author_id', ''),
                    'engagement_score': engagement,
                    'url': f"https://twitter.com/i/status/{tweet_data.get('id', '')}"
                }
                
                parsed_posts.append(parsed_post)
                
            except Exception as e:
                self.logger.debug(f"Error parsing tweet: {e}")
                continue
        
        return parsed_posts
    
    def search_specific_ticker(self, ticker: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for tweets mentioning a specific ticker"""
        if not self.api_client:
            return []
        
        query = f"${ticker} -is:retweet lang:en"
        
        try:
            tweets = tweepy.Paginator(
                self.api_client.search_recent_tweets,
                query=query,
                max_results=min(100, limit),
                tweet_fields=['created_at', 'public_metrics']
            ).flatten(limit=limit)
            
            tweet_data = []
            for tweet in tweets:
                data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'metrics': tweet.public_metrics if hasattr(tweet, 'public_metrics') else {},
                    'source': 'twitter'
                }
                tweet_data.append(data)
            
            return self.parse_posts(tweet_data)
            
        except Exception as e:
            self.logger.error(f"Error searching for ticker {ticker}: {e}")
            return [] 