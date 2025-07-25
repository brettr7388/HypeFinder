import praw
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base_fetcher import BaseFetcher

class RedditFetcher(BaseFetcher):
    """Fetches posts from relevant financial subreddits"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.reddit_client = self._setup_reddit_client()
        
        # Default subreddits to monitor
        self.subreddits = config.get('subreddits', [
            'wallstreetbets',
            'cryptocurrency', 
            'memeeconomy',
            'stockmarket',
            'investing',
            'pennystocks',
            'SecurityAnalysis',
            'stocks',
            'CryptoMoonShots',
            'altcoin',
            'ethtrader',
            'bitcoin'
        ])
        
        # Keywords that indicate financial discussion
        self.financial_keywords = [
            'buy', 'sell', 'hold', 'moon', 'rocket', 'bullish', 'bearish',
            'calls', 'puts', 'options', 'yolo', 'diamond hands', 'paper hands',
            'squeeze', 'pump', 'dump', 'hodl', 'dip', 'rally', 'ath',
            'resistance', 'support', 'breakout', 'earnings', 'dd'
        ]
    
    def _setup_reddit_client(self) -> Optional[praw.Reddit]:
        """Initialize Reddit API client"""
        try:
            client_id = self.config.get('client_id')
            client_secret = self.config.get('client_secret')
            user_agent = self.config.get('user_agent', 'HypeFinder/1.0')
            
            if not all([client_id, client_secret]):
                self.logger.error("Missing Reddit API credentials")
                return None
            
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            
            # Test connection
            try:
                # Simple test to verify connection
                list(reddit.subreddit('wallstreetbets').hot(limit=1))
                self.logger.info("Reddit API connection successful")
                return reddit
            except Exception as e:
                self.logger.error(f"Reddit API authentication failed: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to setup Reddit client: {e}")
            return None
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch posts from multiple subreddits"""
        if not self.reddit_client:
            self.logger.error("Reddit client not available")
            return []
        
        all_posts = []
        max_posts_per_subreddit = self.config.get('max_posts_per_subreddit', 100)
        
        for subreddit_name in self.subreddits:
            try:
                self.logger.info(f"Fetching posts from r/{subreddit_name}")
                subreddit_posts = self._fetch_subreddit_posts(
                    subreddit_name, 
                    max_posts_per_subreddit
                )
                all_posts.extend(subreddit_posts)
                
                # Rate limiting
                self.rate_limit_sleep()
                
            except Exception as e:
                self.logger.warning(f"Error fetching from r/{subreddit_name}: {e}")
                continue
        
        self.logger.info(f"Fetched {len(all_posts)} total Reddit posts")
        return all_posts
    
    def _fetch_subreddit_posts(self, subreddit_name: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch posts from a specific subreddit"""
        posts = []
        
        try:
            subreddit = self.reddit_client.subreddit(subreddit_name)
            
            # Get hot posts (most engagement recently)
            hot_posts = list(subreddit.hot(limit=limit//2))
            
            # Get new posts (most recent)
            new_posts = list(subreddit.new(limit=limit//2))
            
            # Combine and process posts
            for post in hot_posts + new_posts:
                try:
                    # Skip certain post types
                    if post.stickied or post.distinguished:
                        continue
                    
                    # Filter for relevant content
                    if not self._is_relevant_post(post):
                        continue
                    
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'selftext': post.selftext,
                        'author': str(post.author) if post.author else '[deleted]',
                        'created_utc': post.created_utc,
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'num_comments': post.num_comments,
                        'subreddit': subreddit_name,
                        'url': f"https://reddit.com{post.permalink}",
                        'source': 'reddit',
                        'is_self': post.is_self,
                        'flair_text': post.link_flair_text
                    }
                    
                    # Add top comments if available
                    post_data['top_comments'] = self._get_top_comments(post, limit=5)
                    
                    posts.append(post_data)
                    
                except Exception as e:
                    self.logger.debug(f"Error processing post {post.id}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error accessing subreddit r/{subreddit_name}: {e}")
        
        return posts
    
    def _is_relevant_post(self, post) -> bool:
        """Check if post is relevant for financial analysis"""
        # Combine title and self text for analysis
        full_text = f"{post.title} {post.selftext}".lower()
        
        # Check for ticker symbols ($AAPL format)
        if '$' in full_text:
            return True
        
        # Check for financial keywords
        for keyword in self.financial_keywords:
            if keyword in full_text:
                return True
        
        # Check for crypto mentions
        crypto_terms = ['crypto', 'bitcoin', 'btc', 'eth', 'ethereum', 'altcoin', 'defi']
        for term in crypto_terms:
            if term in full_text:
                return True
        
        return False
    
    def _get_top_comments(self, post, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top comments from a post"""
        comments = []
        
        try:
            # Replace "more comments" objects to get actual comments
            post.comments.replace_more(limit=0)
            
            # Get top-level comments sorted by score
            top_comments = sorted(post.comments, key=lambda x: x.score, reverse=True)[:limit]
            
            for comment in top_comments:
                try:
                    # Skip deleted comments
                    if not comment.author or comment.body in ['[deleted]', '[removed]']:
                        continue
                    
                    comment_data = {
                        'id': comment.id,
                        'body': comment.body,
                        'author': str(comment.author),
                        'score': comment.score,
                        'created_utc': comment.created_utc
                    }
                    comments.append(comment_data)
                    
                except Exception as e:
                    self.logger.debug(f"Error processing comment: {e}")
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Error fetching comments for post {post.id}: {e}")
        
        return comments
    
    def parse_posts(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse Reddit data into standardized format"""
        parsed_posts = []
        
        for post_data in raw_data:
            try:
                # Combine title and selftext for full content
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                full_text = f"{title}. {selftext}".strip()
                
                # Clean the text
                cleaned_text = self.clean_text(full_text)
                
                if not cleaned_text:
                    continue
                
                # Calculate engagement score
                score = post_data.get('score', 0)
                num_comments = post_data.get('num_comments', 0)
                upvote_ratio = post_data.get('upvote_ratio', 0.5)
                
                # Weighted engagement score
                engagement_score = (score * upvote_ratio) + (num_comments * 2)
                
                # Convert timestamp
                timestamp = None
                if post_data.get('created_utc'):
                    timestamp = datetime.fromtimestamp(post_data['created_utc']).isoformat()
                
                parsed_post = {
                    'id': post_data.get('id', ''),
                    'text': cleaned_text,
                    'source': 'reddit',
                    'timestamp': timestamp,
                    'author': post_data.get('author', ''),
                    'engagement_score': engagement_score,
                    'url': post_data.get('url', ''),
                    'subreddit': post_data.get('subreddit', ''),
                    'score': score,
                    'num_comments': num_comments,
                    'upvote_ratio': upvote_ratio,
                    'flair': post_data.get('flair_text', '')
                }
                
                # Add comments as separate posts
                comments = post_data.get('top_comments', [])
                for comment in comments:
                    comment_text = self.clean_text(comment.get('body', ''))
                    if comment_text and len(comment_text) > 20:  # Minimum comment length
                        comment_timestamp = None
                        if comment.get('created_utc'):
                            comment_timestamp = datetime.fromtimestamp(comment['created_utc']).isoformat()
                        
                        comment_post = {
                            'id': f"{post_data.get('id', '')}_comment_{comment.get('id', '')}",
                            'text': comment_text,
                            'source': 'reddit_comment',
                            'timestamp': comment_timestamp,
                            'author': comment.get('author', ''),
                            'engagement_score': comment.get('score', 0),
                            'url': post_data.get('url', ''),
                            'subreddit': post_data.get('subreddit', ''),
                            'parent_post_id': post_data.get('id', '')
                        }
                        parsed_posts.append(comment_post)
                
                parsed_posts.append(parsed_post)
                
            except Exception as e:
                self.logger.debug(f"Error parsing Reddit post: {e}")
                continue
        
        return parsed_posts
    
    def search_specific_ticker(self, ticker: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for posts mentioning a specific ticker across all subreddits"""
        if not self.reddit_client:
            return []
        
        all_posts = []
        search_query = f"${ticker}"
        
        for subreddit_name in self.subreddits:
            try:
                subreddit = self.reddit_client.subreddit(subreddit_name) 
                
                # Search within the subreddit
                search_results = list(subreddit.search(
                    search_query, 
                    sort='hot',
                    time_filter='week',
                    limit=limit//len(self.subreddits)
                ))
                
                for post in search_results:
                    try:
                        post_data = {
                            'id': post.id,
                            'title': post.title,
                            'selftext': post.selftext,
                            'author': str(post.author) if post.author else '[deleted]',
                            'created_utc': post.created_utc,
                            'score': post.score,
                            'num_comments': post.num_comments,
                            'subreddit': subreddit_name,
                            'url': f"https://reddit.com{post.permalink}",
                            'source': 'reddit',
                            'top_comments': self._get_top_comments(post, limit=3)
                        }
                        all_posts.append(post_data)
                        
                    except Exception as e:
                        self.logger.debug(f"Error processing search result: {e}")
                        continue
                
                self.rate_limit_sleep()
                
            except Exception as e:
                self.logger.warning(f"Error searching r/{subreddit_name} for {ticker}: {e}")
                continue
        
        return self.parse_posts(all_posts)
    
    def get_subreddit_hot_tickers(self, subreddit_name: str = 'wallstreetbets', limit: int = 50) -> List[Dict[str, Any]]:
        """Get hot posts from a specific subreddit likely to contain tickers"""
        if not self.reddit_client:
            return []
        
        try:
            subreddit = self.reddit_client.subreddit(subreddit_name)
            hot_posts = list(subreddit.hot(limit=limit))
            
            # Filter for posts likely to contain ticker mentions
            relevant_posts = []
            for post in hot_posts:
                if self._is_relevant_post(post):
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'selftext': post.selftext,
                        'author': str(post.author) if post.author else '[deleted]',
                        'created_utc': post.created_utc,
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'subreddit': subreddit_name,
                        'url': f"https://reddit.com{post.permalink}",
                        'source': 'reddit',
                        'top_comments': self._get_top_comments(post, limit=5)
                    }
                    relevant_posts.append(post_data)
            
            return self.parse_posts(relevant_posts)
            
        except Exception as e:
            self.logger.error(f"Error fetching hot tickers from r/{subreddit_name}: {e}")
            return [] 