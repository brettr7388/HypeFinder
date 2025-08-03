import re
from typing import List, Dict, Set, Tuple
from collections import Counter
from utils.logger import setup_logger
from utils.file_utils import load_ticker_list

class TickerParser:
    """Extracts and validates ticker symbols from text"""
    
    def __init__(self):
        self.logger = setup_logger('TickerParser')
        
        # Load known ticker symbols
        self.known_tickers = set(load_ticker_list())
        
        # Regex patterns for ticker extraction
        self.ticker_patterns = [
            r'\$([A-Z]{1,5})\b',           # $AAPL format
            r'\b([A-Z]{2,5})\s+(?:stock|shares?|ticker)\b',  # "AAPL stock"
            r'\b(?:buy|sell|long|short)\s+([A-Z]{2,5})\b',   # "buy AAPL"
        ]
        
        # Crypto-specific patterns
        self.crypto_patterns = [
            r'\b([A-Z]{3,5})(?:USD|BTC|ETH)\b',  # DOGEBTC, ADAUSD
            r'\b(BTC|ETH|ADA|DOT|LINK|LTC|XRP|BCH|BNB|SOL|DOGE|SHIB)\b',  # Common crypto
        ]
        
        # Words to exclude (common false positives)
        self.exclude_words = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN',
            'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BUT', 'HAVE', 'THIS', 'WILL',
            'FROM', 'THEY', 'KNOW', 'WANT', 'BEEN', 'GOOD', 'MUCH', 'SOME',
            'TIME', 'VERY', 'WHEN', 'COME', 'HERE', 'HOW', 'JUST', 'LIKE',
            'LONG', 'MAKE', 'MANY', 'OVER', 'SUCH', 'TAKE', 'THAN', 'THEM',
            'WELL', 'WERE', 'WHAT', 'YOUR', 'WAY', 'WHO', 'BOY', 'DID', 'ITS',
            'LET', 'OLD', 'SEE', 'NOW', 'GET', 'MAN', 'NEW', 'MAY', 'SAY',
            'USE', 'HIM', 'DAY', 'TOO', 'ANY', 'MY', 'SHE', 'PUT', 'END',
            'WHY', 'TRY', 'GOD', 'SIX', 'DOG', 'EAT', 'AGO', 'SIT', 'FUN',
            'BAD', 'YES', 'YET', 'ARM', 'FAR', 'OFF', 'ILL', 'OWN', 'UNDER',
            'READ', 'LAST', 'NEVER', 'US', 'LEFT', 'FIND', 'LIFE', 'WRITE',
            'WORK', 'PART', 'TAKE', 'PLACE', 'MADE', 'LIVE', 'WHERE', 'AFTER',
            'BACK', 'LITTLE', 'ONLY', 'ROUND', 'YEAR', 'CAME', 'SHOW', 'EVERY',
            'GOOD', 'ME', 'GIVE', 'OUR', 'UNDER', 'NAME', 'VERY', 'THROUGH',
            'JUST', 'FORM', 'SENTENCE', 'GREAT', 'THINK', 'HELP', 'LOW', 'LINE',
            'DIFFER', 'TURN', 'CAUSE', 'MUCH', 'MEAN', 'BEFORE', 'MOVE', 'RIGHT',
            'SAME', 'TELL', 'DOES', 'SET', 'THREE', 'WANT', 'AIR', 'WELL',
            'ALSO', 'PLAY', 'SMALL', 'END', 'HOME', 'HAND', 'LARGE', 'SPELL',
            'ADD', 'EVEN', 'LAND', 'HERE', 'MUST', 'BIG', 'HIGH', 'SUCH', 'FOLLOW',
            'ACT', 'WHY', 'ASK', 'MEN', 'CHANGE', 'WENT', 'LIGHT', 'KIND', 'OFF',
            'NEED', 'HOUSE', 'PICTURE', 'TRY', 'AGAIN', 'ANIMAL', 'POINT', 'MOTHER',
            'WORLD', 'NEAR', 'BUILD', 'SELF', 'EARTH', 'FATHER', 'HEAD', 'STAND',
            'OWN', 'PAGE', 'SHOULD', 'COUNTRY', 'FOUND', 'ANSWER', 'SCHOOL',
            'GROW', 'STUDY', 'STILL', 'LEARN', 'PLANT', 'COVER', 'FOOD', 'SUN',
            'FOUR', 'BETWEEN', 'STATE', 'KEEP', 'EYE', 'NEVER', 'LAST', 'LET',
            'THOUGHT', 'CITY', 'TREE', 'CROSS', 'FARM', 'HARD', 'START', 'MIGHT',
            'STORY', 'SAW', 'FAR', 'SEA', 'DRAW', 'LEFT', 'LATE', 'RUN', 'WHILE',
            'REAL', 'OPEN', 'WALK', 'SEEM', 'TOGETHER', 'NEXT', 'WHITE', 'CHILDREN',
            'BEGINNING', 'GOT', 'LOOK', 'EXAMPLE', 'BEING', 'NOTHING', 'CALLED',
            'IDEA', 'FISH', 'MOUNTAIN', 'NORTH', 'ONCE', 'BASE', 'HEAR', 'HORSE',
            'CUT', 'SURE', 'WATCH', 'COLOR', 'FACE', 'WOOD', 'MAIN', 'ENOUGH',
            'PLAIN', 'GIRL', 'USUAL', 'YOUNG', 'READY', 'ABOVE', 'EVER', 'RED',
            'LIST', 'THOUGH', 'FEEL', 'TALK', 'BIRD', 'SOON', 'BODY', 'MUSIC',
            'UNTIL', 'FAMILY', 'LEAVE', 'OFTEN', 'BOOK', 'THOSE', 'BOTH', 'MARK',
            'LETTER', 'MILE', 'RIVER', 'CAR', 'FEET', 'CARE', 'SECOND', 'GROUP',
            'CARRY', 'TOOK', 'RAIN', 'SIDE', 'REAL', 'EAT', 'ROOM', 'FRIEND',
            'BEGAN', 'IDEA', 'FISH', 'MOUNTAIN', 'STOP', 'ONCE', 'BASE', 'HEAR',
            'HORSE', 'CUT', 'SURE', 'WATCH', 'COLOR', 'FACE', 'WOOD', 'MAIN',
            'OPEN', 'SEEM', 'TOGETHER', 'NEXT', 'WHITE', 'CHILDREN', 'BEGINNING',
            'GOT', 'WALK', 'EXAMPLE', 'EASE', 'PAPER', 'OFTEN', 'ALWAYS', 'MUSIC',
            'THOSE', 'BOTH', 'MARK', 'OFTEN', 'LETTER', 'UNTIL', 'MILE', 'RIVER',
            'CAR', 'FEET', 'CARE', 'SECOND', 'ENOUGH', 'PLAIN', 'GIRL', 'USUAL',
            'YOUNG', 'READY', 'ABOVE', 'EVER', 'RED', 'LIST', 'THOUGH', 'FEEL',
            'TALK', 'BIRD', 'SOON', 'BODY', 'MUSIC', 'LEAVE', 'FAMILY', 'STARTED',
            'REALLY', 'HIGH', 'FIELD', 'SEVERAL', 'DURING', 'POSSIBLE', 'CAME',
            # Add the problematic words you found
            'TERM', 'CALLS', 'PER', 'FEW', 'MORE', 'TRUMP' , 'BNB' , 'IN' , 'DYING' , 'AN' , 'DD' , 'ETH' , 'BTC' , 'AT' , 'DOT' , 'NICE' , 'AS' , 'MOONS' , 'VISAS' , 'RTA' , 'RATES' , 'POST' , 'LINK' , 'BUY' , 'BY' , 'LESS' , 'TECH' , 'LYC' , 'BEACH' , 'RANGE' , 'TO' , 'STUFF' , 'COVID' , 'OF' , 'USING' , 'AHEAD' , 'VALID'         }
        
        # Common stock exchange suffixes to remove
        self.exchange_suffixes = {'.TO', '.V', '.L', '.PA', '.DE', '.HK'}
    
    def extract_tickers_from_text(self, text: str) -> List[str]:
        """Extract potential ticker symbols from text"""
        if not text:
            return []
        
        text = text.upper()
        extracted_tickers = set()
        
        # Apply all ticker patterns
        for pattern in self.ticker_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            extracted_tickers.update(matches)
        
        # Apply crypto patterns
        for pattern in self.crypto_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            extracted_tickers.update(matches)
        
        # Clean and validate tickers
        valid_tickers = []
        for ticker in extracted_tickers:
            cleaned_ticker = self.clean_ticker(ticker)
            if self.is_valid_ticker(cleaned_ticker):
                valid_tickers.append(cleaned_ticker)
        
        return list(set(valid_tickers))  # Remove duplicates
    
    def clean_ticker(self, ticker: str) -> str:
        """Clean and normalize ticker symbol"""
        if not ticker:
            return ""
        
        # Remove $ prefix and common suffixes
        ticker = ticker.strip().upper()
        ticker = ticker.lstrip('$')
        
        # Remove exchange suffixes
        for suffix in self.exchange_suffixes:
            if ticker.endswith(suffix):
                ticker = ticker[:-len(suffix)]
                break
        
        return ticker
    
    def is_valid_ticker(self, ticker: str) -> bool:
        """Validate if a string is likely a valid ticker symbol"""
        if not ticker:
            return False
        
        # Length check - most tickers are 2-5 characters
        if len(ticker) < 2 or len(ticker) > 5:
            return False
        
        # Must be all uppercase letters
        if not ticker.isalpha():
            return False
        
        # Exclude common words
        if ticker in self.exclude_words:
            return False
        
        # Additional validation for common false positives
        common_false_positives = {
            'TERM', 'CALLS', 'PER', 'FEW', 'MORE', 'TRUMP', 'CHEAP', 'TAILS', 'THAT', 'HAUL', 'WITH', 'INTO',
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN',
            'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'HAVE', 'THIS', 'WILL',
            'FROM', 'THEY', 'KNOW', 'WANT', 'BEEN', 'GOOD', 'MUCH', 'SOME',
            'TIME', 'VERY', 'WHEN', 'COME', 'HERE', 'HOW', 'JUST', 'LIKE',
            'LONG', 'MAKE', 'MANY', 'OVER', 'SUCH', 'TAKE', 'THAN', 'THEM',
            'WELL', 'WERE', 'WHAT', 'YOUR', 'WAY', 'WHO', 'BOY', 'DID', 'ITS',
            'LET', 'OLD', 'SEE', 'NOW', 'GET', 'MAN', 'NEW', 'MAY', 'SAY',
            'USE', 'HIM', 'DAY', 'TOO', 'ANY', 'MY', 'SHE', 'PUT', 'END',
            'WHY', 'TRY', 'GOD', 'SIX', 'DOG', 'EAT', 'AGO', 'SIT', 'FUN',
            'BAD', 'YES', 'YET', 'ARM', 'FAR', 'OFF', 'ILL', 'OWN', 'UNDER',
            'READ', 'LAST', 'NEVER', 'US', 'LEFT', 'FIND', 'LIFE', 'WRITE',
            'WORK', 'PART', 'TAKE', 'PLACE', 'MADE', 'LIVE', 'WHERE', 'AFTER',
            'BACK', 'LITTLE', 'ONLY', 'ROUND', 'YEAR', 'CAME', 'SHOW', 'EVERY',
            'GOOD', 'ME', 'GIVE', 'OUR', 'UNDER', 'NAME', 'VERY', 'THROUGH',
            'JUST', 'FORM', 'SENTENCE', 'GREAT', 'THINK', 'HELP', 'LOW', 'LINE',
            'DIFFER', 'TURN', 'CAUSE', 'MUCH', 'MEAN', 'BEFORE', 'MOVE', 'RIGHT',
            'SAME', 'TELL', 'DOES', 'SET', 'THREE', 'WANT', 'AIR', 'WELL',
            'ALSO', 'PLAY', 'SMALL', 'END', 'HOME', 'HAND', 'LARGE', 'SPELL',
            'ADD', 'EVEN', 'LAND', 'HERE', 'MUST', 'BIG', 'HIGH', 'SUCH', 'FOLLOW',
            'ACT', 'WHY', 'ASK', 'MEN', 'CHANGE', 'WENT', 'LIGHT', 'KIND', 'OFF',
            'NEED', 'HOUSE', 'PICTURE', 'TRY', 'AGAIN', 'ANIMAL', 'POINT', 'MOTHER',
            'WORLD', 'NEAR', 'BUILD', 'SELF', 'EARTH', 'FATHER', 'HEAD', 'STAND',
            'OWN', 'PAGE', 'SHOULD', 'COUNTRY', 'FOUND', 'ANSWER', 'SCHOOL',
            'GROW', 'STUDY', 'STILL', 'LEARN', 'PLANT', 'COVER', 'FOOD', 'SUN',
            'FOUR', 'BETWEEN', 'STATE', 'KEEP', 'EYE', 'NEVER', 'LAST', 'LET',
            'THOUGHT', 'CITY', 'TREE', 'CROSS', 'FARM', 'HARD', 'START', 'MIGHT',
            'STORY', 'SAW', 'FAR', 'SEA', 'DRAW', 'LEFT', 'LATE', 'RUN', 'WHILE',
            'REAL', 'OPEN', 'WALK', 'SEEM', 'TOGETHER', 'NEXT', 'WHITE', 'CHILDREN',
            'BEGINNING', 'GOT', 'LOOK', 'EXAMPLE', 'BEING', 'NOTHING', 'CALLED',
            'IDEA', 'FISH', 'MOUNTAIN', 'NORTH', 'ONCE', 'BASE', 'HEAR', 'HORSE',
            'CUT', 'SURE', 'WATCH', 'COLOR', 'FACE', 'WOOD', 'MAIN', 'ENOUGH',
            'PLAIN', 'GIRL', 'USUAL', 'YOUNG', 'READY', 'ABOVE', 'EVER', 'RED',
            'LIST', 'THOUGH', 'FEEL', 'TALK', 'BIRD', 'SOON', 'BODY', 'MUSIC',
            'UNTIL', 'FAMILY', 'LEAVE', 'OFTEN', 'BOOK', 'THOSE', 'BOTH', 'MARK',
            'LETTER', 'MILE', 'RIVER', 'CAR', 'FEET', 'CARE', 'SECOND', 'GROUP',
            'CARRY', 'TOOK', 'RAIN', 'SIDE', 'REAL', 'EAT', 'ROOM', 'FRIEND',
            'BEGAN', 'IDEA', 'FISH', 'MOUNTAIN', 'STOP', 'ONCE', 'BASE', 'HEAR',
            'HORSE', 'CUT', 'SURE', 'WATCH', 'COLOR', 'FACE', 'WOOD', 'MAIN',
            'OPEN', 'SEEM', 'TOGETHER', 'NEXT', 'WHITE', 'CHILDREN', 'BEGINNING',
            'GOT', 'WALK', 'EXAMPLE', 'EASE', 'PAPER', 'OFTEN', 'ALWAYS', 'MUSIC',
            'THOSE', 'BOTH', 'MARK', 'OFTEN', 'LETTER', 'UNTIL', 'MILE', 'RIVER',
            'CAR', 'FEET', 'CARE', 'SECOND', 'ENOUGH', 'PLAIN', 'GIRL', 'USUAL',
            'YOUNG', 'READY', 'ABOVE', 'EVER', 'RED', 'LIST', 'THOUGH', 'FEEL',
            'TALK', 'BIRD', 'SOON', 'BODY', 'MUSIC', 'LEAVE', 'FAMILY', 'STARTED',
            'REALLY', 'HIGH', 'FIELD', 'SEVERAL', 'DURING', 'POSSIBLE', 'CAME',
        }
        
        if ticker in common_false_positives:
            return False
        
        # Check against known tickers list (optional validation)
        # If we have a comprehensive list, require match; otherwise, allow unknown tickers
        if len(self.known_tickers) > 100:  # If we have a good ticker list
            return ticker in self.known_tickers
        
        return True
    
    def extract_tickers_from_posts(self, posts: List[Dict]) -> Dict[str, List[Dict]]:
        """Extract tickers from multiple posts and group by ticker"""
        ticker_posts = {}
        
        for post in posts:
            text = post.get('text', '')
            tickers = self.extract_tickers_from_text(text)
            
            for ticker in tickers:
                if ticker not in ticker_posts:
                    ticker_posts[ticker] = []
                
                # Add post with ticker mention
                post_with_ticker = post.copy()
                post_with_ticker['mentioned_ticker'] = ticker
                ticker_posts[ticker].append(post_with_ticker)
        
        return ticker_posts
    
    def get_ticker_mention_counts(self, posts: List[Dict]) -> Counter:
        """Count ticker mentions across all posts"""
        all_tickers = []
        
        for post in posts:
            text = post.get('text', '')
            tickers = self.extract_tickers_from_text(text)
            all_tickers.extend(tickers)
        
        return Counter(all_tickers)
    
    def filter_by_mention_threshold(self, ticker_counts: Counter, min_mentions: int = 5) -> Dict[str, int]:
        """Filter tickers that meet minimum mention threshold"""
        return {ticker: count for ticker, count in ticker_counts.items() 
                if count >= min_mentions}
    
    def get_ticker_context(self, posts: List[Dict], ticker: str, context_window: int = 50) -> List[str]:
        """Extract context around ticker mentions for sentiment analysis"""
        contexts = []
        
        for post in posts:
            text = post.get('text', '')
            if ticker in text.upper():
                # Find ticker position and extract context
                text_upper = text.upper()
                ticker_pos = text_upper.find(ticker)
                if ticker_pos != -1:
                    start = max(0, ticker_pos - context_window)
                    end = min(len(text), ticker_pos + len(ticker) + context_window)
                    context = text[start:end].strip()
                    contexts.append(context)
        
        return contexts 