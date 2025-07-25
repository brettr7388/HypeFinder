from typing import Dict, List, Any, Tuple
from textblob import TextBlob
import re
from collections import Counter
from utils.logger import setup_logger
from parser.text_cleaner import TextCleaner

class SentimentScorer:
    """Calculates sentiment scores for ticker mentions"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = setup_logger('SentimentScorer')
        self.text_cleaner = TextCleaner()
        
        # Sentiment keywords and weights
        self.positive_keywords = {
            # Strong positive
            'moon': 3.0, 'rocket': 3.0, 'bullish': 2.5, 'bull': 2.0,
            'buy': 2.0, 'long': 2.0, 'calls': 1.5, 'pump': 2.0,
            'diamond hands': 2.5, 'hold': 1.5, 'hodl': 2.0,
            'breakout': 2.0, 'rally': 2.0, 'surge': 2.5,
            'gains': 2.0, 'profit': 2.0, 'up': 1.5, 'rise': 1.5,
            'green': 1.5, 'winning': 2.0, 'success': 2.0,
            'strong': 1.8, 'solid': 1.8, 'good': 1.5, 'great': 2.0,
            'excellent': 2.5, 'amazing': 2.5, 'love': 2.0,
            'bullrun': 2.5, 'mooning': 3.0, 'lambo': 2.5,
            'tendies': 2.0, 'printing': 2.0, 'brrr': 1.5,
            
            # Moderate positive
            'positive': 1.5, 'optimistic': 1.8, 'confident': 1.8,
            'potential': 1.2, 'promising': 1.8, 'opportunity': 1.5,
            'undervalued': 1.8, 'cheap': 1.2, 'dip': 1.0,
            'support': 1.2, 'bounce': 1.5, 'recovery': 1.8,
            'upgrade': 1.8, 'beat': 1.5, 'outperform': 2.0,
            'momentum': 1.5, 'volume': 1.2, 'interest': 1.0
        }
        
        self.negative_keywords = {
            # Strong negative
            'crash': -3.0, 'dump': -2.5, 'bearish': -2.5, 'bear': -2.0,
            'sell': -2.0, 'short': -2.0, 'puts': -1.5, 'collapse': -3.0,
            'paper hands': -2.0, 'panic': -2.5, 'fear': -2.0,
            'drop': -2.0, 'fall': -2.0, 'plunge': -2.5, 'tank': -2.5,
            'losses': -2.0, 'loss': -2.0, 'down': -1.5, 'red': -1.5,
            'bad': -1.5, 'terrible': -2.5, 'awful': -2.5, 'hate': -2.0,
            'disaster': -3.0, 'dead': -2.5, 'rekt': -2.5, 'rug': -3.0,
            'scam': -3.0, 'fraud': -3.0, 'ponzi': -3.0,
            
            # Moderate negative
            'negative': -1.5, 'pessimistic': -1.8, 'concerned': -1.5,
            'worried': -1.8, 'doubt': -1.5, 'uncertain': -1.2,
            'overvalued': -1.8, 'expensive': -1.2, 'risky': -1.5,
            'resistance': -1.2, 'rejection': -1.5, 'decline': -1.8,
            'downgrade': -1.8, 'miss': -1.5, 'underperform': -2.0,
            'weak': -1.5, 'poor': -1.8, 'disappointing': -2.0
        }
        
        # Context modifiers
        self.intensifiers = {
            'very': 1.5, 'extremely': 2.0, 'really': 1.3, 'super': 1.8,
            'incredibly': 2.0, 'absolutely': 1.8, 'totally': 1.5,
            'completely': 1.8, 'highly': 1.5, 'massively': 2.0
        }
        
        self.diminishers = {
            'slightly': 0.5, 'somewhat': 0.7, 'little': 0.6, 'bit': 0.6,
            'kind of': 0.7, 'sort of': 0.7, 'maybe': 0.5, 'possibly': 0.6
        }
        
        self.negators = {
            'not', 'no', 'never', 'none', 'nothing', 'neither', 'nowhere',
            'nobody', 'hardly', 'scarcely', 'barely', 'rarely'
        }
    
    def analyze_text_sentiment(self, text: str) -> Tuple[float, float]:
        """Analyze sentiment using TextBlob (returns polarity, subjectivity)"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity, blob.sentiment.subjectivity
        except Exception as e:
            self.logger.debug(f"TextBlob sentiment analysis failed: {e}")
            return 0.0, 0.0
    
    def calculate_keyword_sentiment(self, text: str, ticker: str = None) -> float:
        """Calculate sentiment using keyword matching with context awareness"""
        if not text:
            return 0.0
        
        # Clean and normalize text
        cleaned_text = self.text_cleaner.clean_for_sentiment_analysis(text)
        words = cleaned_text.lower().split()
        
        sentiment_score = 0.0
        word_count = len(words)
        
        if word_count == 0:
            return 0.0
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Check for multi-word phrases first
            if i < len(words) - 1:
                two_word_phrase = f"{word} {words[i + 1]}"
                if two_word_phrase in self.positive_keywords:
                    score = self.positive_keywords[two_word_phrase]
                    sentiment_score += self._apply_context_modifiers(words, i, score)
                    i += 2
                    continue
                elif two_word_phrase in self.negative_keywords:
                    score = self.negative_keywords[two_word_phrase]
                    sentiment_score += self._apply_context_modifiers(words, i, score)
                    i += 2
                    continue
            
            # Check single words
            if word in self.positive_keywords:
                score = self.positive_keywords[word]
                sentiment_score += self._apply_context_modifiers(words, i, score)
            elif word in self.negative_keywords:
                score = self.negative_keywords[word]
                sentiment_score += self._apply_context_modifiers(words, i, score)
            
            i += 1
        
        # Normalize by text length (to prevent bias toward longer texts)
        normalized_score = sentiment_score / max(1, word_count / 10)  # Per 10 words
        
        # Clamp to reasonable range
        return max(-5.0, min(5.0, normalized_score))
    
    def _apply_context_modifiers(self, words: List[str], position: int, base_score: float) -> float:
        """Apply context modifiers (intensifiers, diminishers, negators)"""
        modified_score = base_score
        
        # Look for modifiers in a window around the sentiment word
        window_size = 3
        start_pos = max(0, position - window_size)
        end_pos = min(len(words), position + window_size + 1)
        
        context_words = words[start_pos:end_pos]
        
        # Check for negators first (they flip the sign)
        negated = False
        for word in context_words:
            if word in self.negators:
                negated = True
                break
        
        if negated:
            modified_score = -modified_score * 0.8  # Negated but slightly reduced
        
        # Apply intensifiers and diminishers
        for word in context_words:
            if word in self.intensifiers:
                modified_score *= self.intensifiers[word]
            elif word in self.diminishers:
                modified_score *= self.diminishers[word]
        
        return modified_score
    
    def calculate_ticker_context_sentiment(self, posts: List[Dict], ticker: str) -> Dict[str, Any]:
        """Calculate sentiment specifically in the context of ticker mentions"""
        if not posts:
            return {'sentiment_score': 0.0, 'confidence': 0.0, 'post_count': 0}
        
        ticker_contexts = []
        
        # Extract contexts around ticker mentions
        for post in posts:
            text = post.get('text', '')
            if ticker.upper() in text.upper():
                # Find ticker position and extract surrounding context
                text_upper = text.upper()
                ticker_positions = []
                start = 0
                while True:
                    pos = text_upper.find(ticker.upper(), start)
                    if pos == -1:
                        break
                    ticker_positions.append(pos)
                    start = pos + 1
                
                for pos in ticker_positions:
                    # Extract context window around ticker
                    context_start = max(0, pos - 100)
                    context_end = min(len(text), pos + len(ticker) + 100)
                    context = text[context_start:context_end]
                    ticker_contexts.append(context)
        
        if not ticker_contexts:
            return {'sentiment_score': 0.0, 'confidence': 0.0, 'post_count': 0}
        
        # Calculate sentiment for each context
        keyword_scores = []
        textblob_scores = []
        
        for context in ticker_contexts:
            keyword_score = self.calculate_keyword_sentiment(context, ticker)
            textblob_polarity, textblob_subjectivity = self.analyze_text_sentiment(context)
            
            keyword_scores.append(keyword_score)
            textblob_scores.append(textblob_polarity)
        
        # Combine keyword and TextBlob scores
        avg_keyword = sum(keyword_scores) / len(keyword_scores)
        avg_textblob = sum(textblob_scores) / len(textblob_scores)
        
        # Weighted combination (keyword sentiment gets more weight for financial content)
        combined_score = (avg_keyword * 0.7) + (avg_textblob * 3.0 * 0.3)  # Scale TextBlob to similar range
        
        # Calculate confidence based on consistency
        keyword_std = self._calculate_std(keyword_scores)
        textblob_std = self._calculate_std(textblob_scores)
        
        # Higher confidence when scores are consistent
        confidence = 1.0 / (1.0 + keyword_std + textblob_std)
        
        return {
            'sentiment_score': combined_score,
            'confidence': confidence,
            'post_count': len(posts),
            'context_count': len(ticker_contexts),
            'keyword_sentiment': avg_keyword,
            'textblob_sentiment': avg_textblob,
            'keyword_std': keyword_std,
            'textblob_std': textblob_std
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def calculate_sentiment_trend(self, posts: List[Dict], ticker: str) -> Dict[str, Any]:
        """Calculate sentiment trend over time"""
        if not posts:
            return {'trend': 'neutral', 'trend_strength': 0.0}
        
        # Sort posts by timestamp
        timestamped_posts = []
        for post in posts:
            timestamp_str = post.get('timestamp')
            if timestamp_str:
                try:
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    timestamped_posts.append((timestamp, post))
                except Exception:
                    continue
        
        if len(timestamped_posts) < 2:
            return {'trend': 'neutral', 'trend_strength': 0.0}
        
        timestamped_posts.sort(key=lambda x: x[0])
        
        # Calculate sentiment for time periods
        total_time = timestamped_posts[-1][0] - timestamped_posts[0][0]
        if total_time.total_seconds() < 3600:  # Less than 1 hour
            return {'trend': 'neutral', 'trend_strength': 0.0}
        
        # Split into early and late periods
        mid_time = timestamped_posts[0][0] + total_time / 2
        
        early_posts = [post for timestamp, post in timestamped_posts if timestamp <= mid_time]
        late_posts = [post for timestamp, post in timestamped_posts if timestamp > mid_time]
        
        early_sentiment = self.calculate_ticker_context_sentiment(early_posts, ticker)
        late_sentiment = self.calculate_ticker_context_sentiment(late_posts, ticker)
        
        early_score = early_sentiment['sentiment_score']
        late_score = late_sentiment['sentiment_score']
        
        trend_change = late_score - early_score
        trend_strength = abs(trend_change)
        
        if trend_change > 0.2:
            trend = 'improving'
        elif trend_change < -0.2:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'trend_strength': trend_strength,
            'early_sentiment': early_score,
            'late_sentiment': late_score,
            'trend_change': trend_change
        }
    
    def calculate_comprehensive_sentiment_score(self, ticker_posts: Dict[str, List[Dict]]) -> Dict[str, Dict[str, Any]]:
        """Calculate comprehensive sentiment scores for all tickers"""
        sentiment_scores = {}
        
        for ticker, posts in ticker_posts.items():
            if not posts:
                sentiment_scores[ticker] = {
                    'sentiment_score': 0.0,
                    'confidence': 0.0,
                    'post_count': 0
                }
                continue
            
            # Calculate main sentiment metrics
            context_sentiment = self.calculate_ticker_context_sentiment(posts, ticker)
            trend_analysis = self.calculate_sentiment_trend(posts, ticker)
            
            # Calculate source-weighted sentiment
            source_weights = {'twitter': 1.0, 'reddit': 1.2, 'reddit_comment': 0.8}
            weighted_sentiment = 0.0
            total_weight = 0.0
            
            for post in posts:
                post_text = post.get('text', '')
                post_sentiment = self.calculate_keyword_sentiment(post_text, ticker)
                source = post.get('source', 'unknown')
                weight = source_weights.get(source, 1.0)
                
                weighted_sentiment += post_sentiment * weight
                total_weight += weight
            
            if total_weight > 0:
                weighted_sentiment /= total_weight
            
            # Combine all sentiment metrics
            final_sentiment = (
                context_sentiment['sentiment_score'] * 0.5 +
                weighted_sentiment * 0.3 +
                (1.0 if trend_analysis['trend'] == 'improving' else 
                 -1.0 if trend_analysis['trend'] == 'declining' else 0.0) * 
                trend_analysis['trend_strength'] * 0.2
            )
            
            sentiment_scores[ticker] = {
                'sentiment_score': final_sentiment,
                'confidence': context_sentiment['confidence'],
                'post_count': len(posts),
                'context_sentiment': context_sentiment['sentiment_score'],
                'weighted_sentiment': weighted_sentiment,
                'trend': trend_analysis['trend'],
                'trend_strength': trend_analysis['trend_strength'],
                'keyword_sentiment': context_sentiment.get('keyword_sentiment', 0.0),
                'textblob_sentiment': context_sentiment.get('textblob_sentiment', 0.0)
            }
        
        return sentiment_scores 