from typing import Dict, List, Any, Tuple
from datetime import datetime
import math
from utils.logger import setup_logger
from .volume_scorer import VolumeScorer
from .sentiment_scorer import SentimentScorer
from parser.ticker_parser import TickerParser

class HypeScorer:
    """Main scorer that combines volume and sentiment to calculate hype scores"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger('HypeScorer')
        
        # Initialize component scorers
        self.volume_scorer = VolumeScorer(config.get('volume_scorer', {}))
        self.sentiment_scorer = SentimentScorer(config.get('sentiment_scorer', {}))
        self.ticker_parser = TickerParser()
        
        # Scoring weights from configuration
        self.volume_weight = config.get('volume_weight', 0.7)
        self.sentiment_weight = config.get('sentiment_weight', 0.3)
        self.min_mentions = config.get('min_mentions', 5)
        self.top_n_tickers = config.get('top_n_tickers', 20)
        
        # Additional scoring parameters
        self.recency_boost = config.get('recency_boost', True)
        self.cross_platform_bonus = config.get('cross_platform_bonus', True)
        self.engagement_multiplier = config.get('engagement_multiplier', True)
        
        # Quality filters
        self.min_sentiment_confidence = config.get('min_sentiment_confidence', 0.1)
        self.exclude_low_engagement = config.get('exclude_low_engagement', True)
        
        self.logger.info(f"Initialized HypeScorer with weights: volume={self.volume_weight}, sentiment={self.sentiment_weight}")
    
    def calculate_hype_scores(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate comprehensive hype scores for all tickers found in posts"""
        if not posts:
            self.logger.warning("No posts provided for hype scoring")
            return []
        
        self.logger.info(f"Calculating hype scores for {len(posts)} posts")
        
        # Extract tickers from posts
        ticker_posts = self.ticker_parser.extract_tickers_from_posts(posts)
        
        if not ticker_posts:
            self.logger.warning("No tickers found in posts")
            return []
        
        self.logger.info(f"Found {len(ticker_posts)} unique tickers")
        
        # Filter tickers by minimum mentions
        filtered_ticker_posts = {}
        for ticker, ticker_post_list in ticker_posts.items():
            if len(ticker_post_list) >= self.min_mentions:
                filtered_ticker_posts[ticker] = ticker_post_list
            else:
                self.logger.debug(f"Filtered out {ticker} (only {len(ticker_post_list)} mentions)")
        
        if not filtered_ticker_posts:
            self.logger.warning(f"No tickers with >= {self.min_mentions} mentions")
            return []
        
        self.logger.info(f"After filtering: {len(filtered_ticker_posts)} tickers remain")
        
        # Calculate volume scores
        volume_scores = self.volume_scorer.calculate_comprehensive_volume_score(filtered_ticker_posts)
        volume_metrics = self.volume_scorer.get_volume_metrics(filtered_ticker_posts)
        
        # Calculate sentiment scores
        sentiment_scores = self.sentiment_scorer.calculate_comprehensive_sentiment_score(filtered_ticker_posts)
        
        # Combine scores
        hype_results = []
        
        for ticker in filtered_ticker_posts.keys():
            volume_score = volume_scores.get(ticker, 0.0)
            sentiment_data = sentiment_scores.get(ticker, {})
            sentiment_score = sentiment_data.get('sentiment_score', 0.0)
            sentiment_confidence = sentiment_data.get('confidence', 0.0)
            
            # Skip tickers with very low sentiment confidence if configured
            if sentiment_confidence < self.min_sentiment_confidence:
                self.logger.debug(f"Skipping {ticker} due to low sentiment confidence: {sentiment_confidence}")
                continue
            
            # Calculate base hype score
            hype_score = (volume_score * self.volume_weight) + (sentiment_score * self.sentiment_weight)
            
            # Apply additional scoring factors
            hype_score = self._apply_scoring_modifiers(
                ticker, 
                hype_score, 
                filtered_ticker_posts[ticker],
                volume_metrics.get(ticker, {}),
                sentiment_data
            )
            
            # Compile comprehensive result
            result = {
                'ticker': ticker,
                'hype_score': hype_score,
                'volume_score': volume_score,
                'sentiment_score': sentiment_score,
                'sentiment_confidence': sentiment_confidence,
                'mention_count': len(filtered_ticker_posts[ticker]),
                'timestamp': datetime.now().isoformat(),
                
                # Volume metrics
                'volume_metrics': volume_metrics.get(ticker, {}),
                
                # Sentiment details
                'sentiment_trend': sentiment_data.get('trend', 'neutral'),
                'sentiment_trend_strength': sentiment_data.get('trend_strength', 0.0),
                'keyword_sentiment': sentiment_data.get('keyword_sentiment', 0.0),
                'textblob_sentiment': sentiment_data.get('textblob_sentiment', 0.0),
                
                # Platform distribution
                'platforms': list(set(post.get('source', '') for post in filtered_ticker_posts[ticker])),
                'platform_count': len(set(post.get('source', '') for post in filtered_ticker_posts[ticker])),
                
                # Sample posts for context
                'sample_posts': self._get_sample_posts(filtered_ticker_posts[ticker], 3)
            }
            
            hype_results.append(result)
        
        # Sort by hype score descending
        hype_results.sort(key=lambda x: x['hype_score'], reverse=True)
        
        # Normalize ranks
        for i, result in enumerate(hype_results):
            result['rank'] = i + 1
        
        # Return top N results
        top_results = hype_results[:self.top_n_tickers]
        
        self.logger.info(f"Generated hype scores for {len(top_results)} top tickers")
        
        return top_results
    
    def _apply_scoring_modifiers(self, ticker: str, base_score: float, posts: List[Dict], 
                                volume_metrics: Dict, sentiment_data: Dict) -> float:
        """Apply additional scoring modifiers based on various factors"""
        modified_score = base_score
        
        # Recency boost - more recent activity gets higher scores
        if self.recency_boost:
            recency_multiplier = self._calculate_recency_multiplier(posts)
            modified_score *= recency_multiplier
        
        # Cross-platform bonus
        if self.cross_platform_bonus:
            platform_count = len(set(post.get('source', '') for post in posts))
            if platform_count > 1:
                cross_platform_multiplier = 1.0 + (platform_count - 1) * 0.15  # 15% boost per additional platform
                modified_score *= cross_platform_multiplier
        
        # Engagement multiplier
        if self.engagement_multiplier:
            avg_engagement = sum(post.get('engagement_score', 0) for post in posts) / len(posts)
            engagement_multiplier = 1.0 + min(avg_engagement / 100.0, 0.5)  # Cap at 50% boost
            modified_score *= engagement_multiplier
        
        # Sentiment confidence boost
        sentiment_confidence = sentiment_data.get('confidence', 0.0)
        confidence_multiplier = 0.8 + (sentiment_confidence * 0.4)  # Range from 0.8 to 1.2
        modified_score *= confidence_multiplier
        
        # Velocity bonus for rapidly growing mentions
        velocity = volume_metrics.get('velocity_per_hour', 0.0)
        if velocity > 2.0:  # More than 2 mentions per hour
            velocity_multiplier = 1.0 + min(velocity / 10.0, 0.3)  # Cap at 30% boost
            modified_score *= velocity_multiplier
        
        # Spike detection bonus
        spike_ratio = volume_metrics.get('spike_ratio', 1.0)
        if spike_ratio > 1.5:  # 50% above average mentions
            spike_multiplier = 1.0 + min((spike_ratio - 1.0) / 5.0, 0.25)  # Cap at 25% boost
            modified_score *= spike_multiplier
        
        return modified_score
    
    def _calculate_recency_multiplier(self, posts: List[Dict]) -> float:
        """Calculate multiplier based on how recent the posts are"""
        if not posts:
            return 1.0
        
        current_time = datetime.now()
        total_recency_score = 0.0
        valid_posts = 0
        
        for post in posts:
            timestamp_str = post.get('timestamp')
            if timestamp_str:
                try:
                    post_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if post_time.tzinfo:
                        post_time = post_time.replace(tzinfo=None)
                    
                    hours_ago = (current_time - post_time).total_seconds() / 3600.0
                    
                    # Exponential decay: newer posts get higher scores
                    recency_score = math.exp(-hours_ago / 12.0)  # Half-life of 12 hours
                    total_recency_score += recency_score
                    valid_posts += 1
                    
                except Exception as e:
                    self.logger.debug(f"Error parsing timestamp for recency: {e}")
                    continue
        
        if valid_posts == 0:
            return 1.0
        
        avg_recency = total_recency_score / valid_posts
        # Convert to multiplier range 0.5 to 1.5
        return 0.5 + avg_recency
    
    def _get_sample_posts(self, posts: List[Dict], count: int = 3) -> List[Dict]:
        """Get sample posts for context, prioritizing high engagement"""
        if not posts:
            return []
        
        # Sort by engagement score descending
        sorted_posts = sorted(posts, key=lambda x: x.get('engagement_score', 0), reverse=True)
        
        sample_posts = []
        for post in sorted_posts[:count]:
            sample_post = {
                'text': post.get('text', '')[:200] + ('...' if len(post.get('text', '')) > 200 else ''),
                'source': post.get('source', ''),
                'engagement_score': post.get('engagement_score', 0),
                'url': post.get('url', ''),
                'timestamp': post.get('timestamp', '')
            }
            sample_posts.append(sample_post)
        
        return sample_posts
    
    def get_scoring_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for the scoring session"""
        if not results:
            return {'total_tickers': 0}
        
        total_mentions = sum(result['mention_count'] for result in results)
        avg_hype_score = sum(result['hype_score'] for result in results) / len(results)
        avg_sentiment = sum(result['sentiment_score'] for result in results) / len(results)
        avg_volume = sum(result['volume_score'] for result in results) / len(results)
        
        # Platform distribution
        all_platforms = []
        for result in results:
            all_platforms.extend(result['platforms'])
        platform_counts = {}
        for platform in all_platforms:
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        # Sentiment trend distribution
        trend_counts = {}
        for result in results:
            trend = result['sentiment_trend']
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        
        return {
            'total_tickers': len(results),
            'total_mentions': total_mentions,
            'avg_hype_score': avg_hype_score,
            'avg_sentiment_score': avg_sentiment,
            'avg_volume_score': avg_volume,
            'top_ticker': results[0]['ticker'] if results else None,
            'top_hype_score': results[0]['hype_score'] if results else 0,
            'platform_distribution': platform_counts,
            'sentiment_trend_distribution': trend_counts,
            'scoring_weights': {
                'volume_weight': self.volume_weight,
                'sentiment_weight': self.sentiment_weight
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def explain_score(self, ticker: str, result: Dict[str, Any]) -> str:
        """Generate human-readable explanation of how the hype score was calculated"""
        explanation = []
        
        explanation.append(f"Hype Score Breakdown for ${ticker}:")
        explanation.append(f"  Final Score: {result['hype_score']:.3f} (Rank #{result['rank']})")
        explanation.append("")
        
        # Volume component
        volume_contrib = result['volume_score'] * self.volume_weight
        explanation.append(f"  Volume Component: {result['volume_score']:.3f} × {self.volume_weight} = {volume_contrib:.3f}")
        explanation.append(f"    - Raw mentions: {result['mention_count']}")
        
        volume_metrics = result.get('volume_metrics', {})
        if volume_metrics:
            explanation.append(f"    - Velocity: {volume_metrics.get('velocity_per_hour', 0):.2f} mentions/hour")
            explanation.append(f"    - Spike ratio: {volume_metrics.get('spike_ratio', 1):.2f}x")
            explanation.append(f"    - Cross-platform boost: {volume_metrics.get('cross_platform_boost', 1):.2f}x")
        
        explanation.append("")
        
        # Sentiment component  
        sentiment_contrib = result['sentiment_score'] * self.sentiment_weight
        explanation.append(f"  Sentiment Component: {result['sentiment_score']:.3f} × {self.sentiment_weight} = {sentiment_contrib:.3f}")
        explanation.append(f"    - Keyword sentiment: {result.get('keyword_sentiment', 0):.3f}")
        explanation.append(f"    - TextBlob sentiment: {result.get('textblob_sentiment', 0):.3f}")
        explanation.append(f"    - Confidence: {result['sentiment_confidence']:.3f}")
        explanation.append(f"    - Trend: {result['sentiment_trend']}")
        
        explanation.append("")
        
        # Platform info
        explanation.append(f"  Platforms: {', '.join(result['platforms'])} ({result['platform_count']} total)")
        
        return "\n".join(explanation) 