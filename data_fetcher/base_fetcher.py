from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time
import requests
from utils.logger import setup_logger

class BaseFetcher(ABC):
    """Base class for data fetchers with common functionality"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(f'{self.__class__.__name__}')
        self.session = requests.Session()
        self.session.timeout = config.get('timeout', 30)
    
    @abstractmethod
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch raw data from the source"""
        pass
    
    @abstractmethod
    def parse_posts(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse raw data into standardized post format"""
        pass
    
    def rate_limit_sleep(self, delay: Optional[int] = None) -> None:
        """Sleep to respect rate limits"""
        sleep_time = delay or self.config.get('rate_limit_delay', 1)
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    def extract_text_content(self, post_data: Dict[str, Any]) -> str:
        """Extract text content from post data - to be overridden by subclasses"""
        return post_data.get('text', '')
    
    def clean_text(self, text: str) -> str:
        """Basic text cleaning"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove URLs
        import re
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        
        return text.strip()
    
    def make_request(self, url: str, headers: Optional[Dict[str, str]] = None, 
                     params: Optional[Dict[str, Any]] = None) -> Optional[requests.Response]:
        """Make HTTP request with error handling and retries"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', retry_delay * (attempt + 1)))
                    self.logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {response.text}")
                    
            except requests.RequestException as e:
                self.logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                    
        return None
    
    def get_standardized_posts(self) -> List[Dict[str, Any]]:
        """Main method to fetch and parse data into standardized format"""
        try:
            self.logger.info(f"Fetching data from {self.__class__.__name__}")
            raw_data = self.fetch_data()
            
            if not raw_data:
                self.logger.warning("No data fetched")
                return []
            
            posts = self.parse_posts(raw_data)
            self.logger.info(f"Successfully parsed {len(posts)} posts")
            return posts
            
        except Exception as e:
            self.logger.error(f"Error in get_standardized_posts: {e}")
            return [] 