from typing import Dict, List, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import math
from utils.logger import setup_logger

class VolumeScorer:
    """Calculates volume-based scoring for ticker symbols"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = setup_logger('VolumeScorer')
        
        # Scoring parameters
        self.time_decay_factor = self.config.get('time_decay_factor', 0.9)
        self.engagement_weight = self.config.get('engagement_weight', 0.3)
        self.source_weights = self.config.get('source_weights', {
            'twitter': 1.0,
            'reddit': 1.2,
            'reddit_comment': 0.8
        })
    
    def calculate_raw_volume(self, ticker_posts: Dict[str, List[Dict]]) -> Dict[str, float]:
        """Calculate raw mention volume for each ticker"""
        volume_scores = {}
        
        for ticker, posts in ticker_posts.items():
            raw_count = len(posts)
            volume_scores[ticker] = float(raw_count)
        
        return volume_scores
    
    def calculate_weighted_volume(self, ticker_posts: Dict[str, List[Dict]]) -> Dict[str, float]:
        """Calculate volume with source weighting and engagement consideration"""
        volume_scores = {}
        
        for ticker, posts in ticker_posts.items():
            weighted_score = 0.0
            
            for post in posts:
                # Base score from source
                source = post.get('source', 'unknown')
                source_weight = self.source_weights.get(source, 1.0)
                
                # Engagement multiplier
                engagement = post.get('engagement_score', 0)
                engagement_multiplier = 1.0 + (engagement * self.engagement_weight / 100.0)
                
                # Combined score for this post
                post_score = source_weight * engagement_multiplier
                weighted_score += post_score
            
            volume_scores[ticker] = weighted_score
        
        return volume_scores
    
    def calculate_time_weighted_volume(self, ticker_posts: Dict[str, List[Dict]]) -> Dict[str, float]:
        """Calculate volume with time decay (recent posts weighted higher)"""
        volume_scores = {}
        current_time = datetime.now()
        
        for ticker, posts in ticker_posts.items():
            time_weighted_score = 0.0
            
            for post in posts:
                # Calculate time decay
                time_weight = 1.0
                timestamp_str = post.get('timestamp')
                
                if timestamp_str:
                    try:
                        post_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        # Remove timezone info for comparison
                        if post_time.tzinfo:
                            post_time = post_time.replace(tzinfo=None)
                        
                        hours_ago = (current_time - post_time).total_seconds() / 3600.0
                        time_weight = math.pow(self.time_decay_factor, hours_ago)
                    except Exception as e:
                        self.logger.debug(f"Error parsing timestamp {timestamp_str}: {e}")
                
                # Source and engagement weights
                source = post.get('source', 'unknown')
                source_weight = self.source_weights.get(source, 1.0)
                
                engagement = post.get('engagement_score', 0)
                engagement_multiplier = 1.0 + (engagement * self.engagement_weight / 100.0)
                
                # Combined score for this post
                post_score = source_weight * engagement_multiplier * time_weight
                time_weighted_score += post_score
            
            volume_scores[ticker] = time_weighted_score
        
        return volume_scores
    
    def calculate_velocity_score(self, ticker_posts: Dict[str, List[Dict]]) -> Dict[str, float]:
        """Calculate mention velocity (mentions per hour in recent period)"""
        velocity_scores = {}
        current_time = datetime.now()
        
        # Look at last 4 hours for velocity calculation
        velocity_window_hours = 4
        
        for ticker, posts in ticker_posts.items():
            recent_posts = []
            
            for post in posts:
                timestamp_str = post.get('timestamp')
                if timestamp_str:
                    try:
                        post_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if post_time.tzinfo:
                            post_time = post_time.replace(tzinfo=None)
                        
                        hours_ago = (current_time - post_time).total_seconds() / 3600.0
                        
                        if hours_ago <= velocity_window_hours:
                            recent_posts.append(post)
                    except Exception as e:
                        self.logger.debug(f"Error parsing timestamp for velocity: {e}")
            
            # Calculate velocity (mentions per hour)
            velocity = len(recent_posts) / velocity_window_hours
            velocity_scores[ticker] = velocity
        
        return velocity_scores
    
    def calculate_spike_detection(self, ticker_posts: Dict[str, List[Dict]]) -> Dict[str, float]:
        """Detect sudden spikes in mention volume"""
        spike_scores = {}
        current_time = datetime.now()
        
        for ticker, posts in ticker_posts.items():
            # Separate posts into time buckets (1-hour intervals)
            hourly_counts = defaultdict(int)
            
            for post in posts:
                timestamp_str = post.get('timestamp')
                if timestamp_str:
                    try:
                        post_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if post_time.tzinfo:
                            post_time = post_time.replace(tzinfo=None)
                        
                        # Round to hour bucket
                        hour_bucket = post_time.replace(minute=0, second=0, microsecond=0)
                        hourly_counts[hour_bucket] += 1
                    except Exception as e:
                        continue
            
            if not hourly_counts:
                spike_scores[ticker] = 0.0
                continue
            
            # Calculate spike score
            counts = list(hourly_counts.values())
            if len(counts) < 2:
                spike_scores[ticker] = 0.0
                continue
            
            avg_count = sum(counts) / len(counts)
            recent_count = max(counts) if counts else 0
            
            # Spike ratio (recent peak vs average)
            spike_ratio = recent_count / avg_count if avg_count > 0 else 1.0
            spike_scores[ticker] = spike_ratio
        
        return spike_scores
    
    def calculate_cross_platform_boost(self, ticker_posts: Dict[str, List[Dict]]) -> Dict[str, float]:
        """Boost score for tickers mentioned across multiple platforms"""
        boost_scores = {}
        
        for ticker, posts in ticker_posts.items():
            sources = set()
            for post in posts:
                source = post.get('source', 'unknown')
                sources.add(source)
            
            # Cross-platform multiplier
            platform_count = len(sources)
            cross_platform_boost = 1.0 + (platform_count - 1) * 0.2  # 20% boost per additional platform
            
            boost_scores[ticker] = cross_platform_boost
        
        return boost_scores
    
    def normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to 0-1 range"""
        if not scores:
            return {}
        
        max_score = max(scores.values())
        min_score = min(scores.values())
        
        if max_score == min_score:
            return {ticker: 1.0 for ticker in scores}
        
        normalized = {}
        for ticker, score in scores.items():
            normalized[ticker] = (score - min_score) / (max_score - min_score)
        
        return normalized
    
    def calculate_comprehensive_volume_score(self, ticker_posts: Dict[str, List[Dict]]) -> Dict[str, float]:
        """Calculate comprehensive volume score combining all metrics"""
        if not ticker_posts:
            return {}
        
        # Calculate individual components
        raw_volume = self.calculate_raw_volume(ticker_posts)
        weighted_volume = self.calculate_weighted_volume(ticker_posts)
        time_weighted = self.calculate_time_weighted_volume(ticker_posts)
        velocity = self.calculate_velocity_score(ticker_posts)
        spike_detection = self.calculate_spike_detection(ticker_posts)
        cross_platform = self.calculate_cross_platform_boost(ticker_posts)
        
        # Normalize individual components
        norm_raw = self.normalize_scores(raw_volume)
        norm_weighted = self.normalize_scores(weighted_volume)
        norm_time = self.normalize_scores(time_weighted)
        norm_velocity = self.normalize_scores(velocity)
        norm_spike = self.normalize_scores(spike_detection)
        
        # Combine with weights
        component_weights = {
            'raw': 0.2,
            'weighted': 0.25,
            'time_weighted': 0.25,
            'velocity': 0.15,
            'spike': 0.15
        }
        
        final_scores = {}
        for ticker in ticker_posts.keys():
            score = (
                norm_raw.get(ticker, 0) * component_weights['raw'] +
                norm_weighted.get(ticker, 0) * component_weights['weighted'] +
                norm_time.get(ticker, 0) * component_weights['time_weighted'] +
                norm_velocity.get(ticker, 0) * component_weights['velocity'] +
                norm_spike.get(ticker, 0) * component_weights['spike']
            )
            
            # Apply cross-platform boost
            score *= cross_platform.get(ticker, 1.0)
            
            final_scores[ticker] = score
        
        return final_scores
    
    def get_volume_metrics(self, ticker_posts: Dict[str, List[Dict]]) -> Dict[str, Dict[str, Any]]:
        """Get detailed volume metrics for each ticker"""
        metrics = {}
        
        raw_vol = self.calculate_raw_volume(ticker_posts)
        weighted_vol = self.calculate_weighted_volume(ticker_posts)
        time_weighted = self.calculate_time_weighted_volume(ticker_posts)
        velocity = self.calculate_velocity_score(ticker_posts)
        spike = self.calculate_spike_detection(ticker_posts)
        cross_platform = self.calculate_cross_platform_boost(ticker_posts)
        
        for ticker in ticker_posts.keys():
            # Calculate source distribution
            sources = Counter()
            total_engagement = 0
            
            for post in ticker_posts[ticker]:
                sources[post.get('source', 'unknown')] += 1
                total_engagement += post.get('engagement_score', 0)
            
            metrics[ticker] = {
                'raw_mentions': raw_vol.get(ticker, 0),
                'weighted_volume': weighted_vol.get(ticker, 0),
                'time_weighted_volume': time_weighted.get(ticker, 0),
                'velocity_per_hour': velocity.get(ticker, 0),
                'spike_ratio': spike.get(ticker, 0),
                'cross_platform_boost': cross_platform.get(ticker, 1.0),
                'total_engagement': total_engagement,
                'platform_distribution': dict(sources),
                'unique_authors': len(set(post.get('author', '') for post in ticker_posts[ticker]))
            }
        
        return metrics 