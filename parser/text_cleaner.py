import re
from typing import List, Optional
import html

class TextCleaner:
    """Utility class for cleaning and normalizing social media text"""
    
    def __init__(self):
        # Common patterns for cleaning
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.mention_pattern = re.compile(r'@\w+')
        self.hashtag_pattern = re.compile(r'#\w+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'[\+]?[1-9]?[0-9]{7,14}')
        self.excessive_whitespace = re.compile(r'\s+')
        self.multiple_punctuation = re.compile(r'[!?.]{3,}')
        
        # Emoji pattern (basic)
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        
        # Reddit-specific patterns
        self.reddit_quote_pattern = re.compile(r'^&gt;.*$', re.MULTILINE)
        self.reddit_edit_pattern = re.compile(r'\*?Edit\s*:.*$', re.IGNORECASE | re.MULTILINE)
        
        # Stock/crypto slang normalization
        self.slang_replacements = {
            'hodl': 'hold',
            'stonks': 'stocks',  
            'tendies': 'profits',
            'diamond hands': 'holding strong',
            'paper hands': 'selling quickly',
            'moon': 'price increase',
            'lambo': 'profits',
            'ape': 'investor',
            'retard': 'investor',  # WSB slang
            'autist': 'investor',  # WSB slang
            'yolo': 'risky investment',
            'fomo': 'fear of missing out',
            'dd': 'due diligence',
            'gains': 'profits',
            'loss porn': 'investment losses',
            'bag holder': 'stuck investor',
            'squeeze': 'price surge',
            'rocket': 'price increase',
            'brrrr': 'money printing',
            'guh': 'loss reaction',
        }
    
    def clean_basic(self, text: str) -> str:
        """Basic text cleaning - remove URLs, excessive whitespace"""
        if not text:
            return ""
        
        # Decode HTML entities  
        text = html.unescape(text)
        
        # Remove URLs
        text = self.url_pattern.sub('', text)
        
        # Remove excessive whitespace
        text = self.excessive_whitespace.sub(' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def clean_social_media(self, text: str, preserve_tickers: bool = True) -> str:
        """Clean social media text while preserving important financial information"""
        if not text:
            return ""
        
        # Start with basic cleaning
        text = self.clean_basic(text)
        
        # Store ticker symbols to preserve them
        tickers = []
        if preserve_tickers:
            tickers = re.findall(r'\$[A-Z]{1,5}\b', text.upper())
        
        # Remove mentions (but not tickers)
        text = self.mention_pattern.sub('', text)
        
        # Handle hashtags - remove # but keep text if it looks like a ticker
        def hashtag_replacer(match):
            hashtag = match.group(0)
            tag_text = hashtag[1:]  # Remove #
            if tag_text.upper() in [t[1:] for t in tickers]:  # If hashtag is a ticker
                return f"${tag_text.upper()}"
            return tag_text  # Keep text without #
        
        text = self.hashtag_pattern.sub(hashtag_replacer, text)
        
        # Remove emails and phone numbers
        text = self.email_pattern.sub('', text)
        text = self.phone_pattern.sub('', text)
        
        # Clean up excessive punctuation
        text = self.multiple_punctuation.sub('...', text)
        
        # Remove emojis (optional - they might have sentiment value)
        # text = self.emoji_pattern.sub('', text)
        
        # Final whitespace cleanup
        text = self.excessive_whitespace.sub(' ', text).strip()
        
        return text
    
    def clean_reddit_post(self, text: str) -> str:
        """Clean Reddit-specific formatting"""
        if not text:
            return ""
        
        # Start with social media cleaning
        text = self.clean_social_media(text)
        
        # Remove Reddit quotes
        text = self.reddit_quote_pattern.sub('', text)
        
        # Remove edit notes
        text = self.reddit_edit_pattern.sub('', text)
        
        # Clean up remaining whitespace
        text = self.excessive_whitespace.sub(' ', text).strip()
        
        return text
    
    def normalize_financial_slang(self, text: str) -> str:
        """Normalize financial/trading slang to standard terms"""
        if not text:
            return ""
        
        text_lower = text.lower()
        
        for slang, replacement in self.slang_replacements.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(slang) + r'\b'
            text_lower = re.sub(pattern, replacement, text_lower)
        
        return text_lower
    
    def extract_sentences(self, text: str) -> List[str]:
        """Split text into sentences for analysis"""
        if not text:
            return []
        
        # Simple sentence splitting on . ! ?
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter short sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Minimum sentence length
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def remove_noise_words(self, text: str) -> str:
        """Remove common noise words that don't add sentiment value"""
        noise_words = [
            'lol', 'lmao', 'omg', 'wtf', 'tbh', 'imo', 'imho', 'afaik',
            'tldr', 'tl;dr', 'fyi', 'btw', 'idk', 'ngl', 'smh'
        ]
        
        for noise in noise_words:
            text = re.sub(r'\b' + re.escape(noise) + r'\b', '', text, flags=re.IGNORECASE)
        
        return self.excessive_whitespace.sub(' ', text).strip()
    
    def preserve_financial_context(self, text: str) -> str:
        """Clean text while preserving financial context and terminology"""
        if not text:
            return ""
        
        # List of financial terms to preserve
        financial_terms = [
            'buy', 'sell', 'hold', 'bullish', 'bearish', 'pump', 'dump',
            'calls', 'puts', 'options', 'strike', 'expiry', 'volume',
            'resistance', 'support', 'breakout', 'dip', 'rally', 'correction',
            'margin', 'leverage', 'short', 'long', 'bull', 'bear', 'market',
            'earnings', 'revenue', 'profit', 'loss', 'eps', 'pe ratio',
            'dividend', 'yield', 'split', 'ipo', 'spac', 'merger', 'acquisition'
        ]
        
        # Store financial terms and their positions
        preserved_terms = {}
        text_lower = text.lower()
        
        for term in financial_terms:
            if term in text_lower:
                preserved_terms[term] = True
        
        # Clean the text
        cleaned = self.clean_social_media(text)
        
        # The financial terms should be preserved through the cleaning process
        return cleaned
    
    def clean_for_sentiment_analysis(self, text: str, normalize_slang: bool = True) -> str:
        """Clean text specifically for sentiment analysis"""
        if not text:
            return ""
        
        # Clean social media content
        text = self.clean_social_media(text, preserve_tickers=True)
        
        # Normalize slang if requested
        if normalize_slang:
            text = self.normalize_financial_slang(text)
        
        # Remove noise words
        text = self.remove_noise_words(text)
        
        # Preserve financial context
        text = self.preserve_financial_context(text)
        
        return text 