#!/usr/bin/env python3
"""
HypeFinder CLI - Main command-line interface
"""

import click
import sys
import os
from datetime import datetime
import json
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from data_fetcher import TwitterFetcher, RedditFetcher
from scorer.hype_scorer import HypeScorer
from utils.logger import setup_logger
from utils.file_utils import save_to_csv, append_to_history, create_sample_ticker_file

class HypeFinder:
    """Main HypeFinder application class"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.logger = setup_logger('HypeFinder', config.get('output.log_level', 'INFO'))
        
        # Initialize components
        self.twitter_fetcher = None
        self.reddit_fetcher = None
        self.hype_scorer = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize data fetchers and scorer"""
        try:
            # Initialize Twitter fetcher
            twitter_config = self.config.get('twitter', {})
            twitter_config.update(self.config.get('scraping', {}))
            
            if self._has_twitter_credentials():
                self.twitter_fetcher = TwitterFetcher(twitter_config)
                self.logger.info("Twitter fetcher initialized")
            else:
                self.logger.warning("Twitter credentials not found - Twitter fetching disabled")
            
            # Initialize Reddit fetcher
            reddit_config = self.config.get('reddit', {})
            reddit_config.update(self.config.get('scraping', {}))
            
            if self._has_reddit_credentials():
                self.reddit_fetcher = RedditFetcher(reddit_config)
                self.logger.info("Reddit fetcher initialized")
            else:
                self.logger.warning("Reddit credentials not found - Reddit fetching disabled")
            
            # Initialize hype scorer
            scoring_config = self.config.get('scoring', {})
            self.hype_scorer = HypeScorer(scoring_config)
            self.logger.info("Hype scorer initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def _has_twitter_credentials(self) -> bool:
        """Check if Twitter credentials are available"""
        twitter_config = self.config.get('twitter', {})
        return bool(twitter_config.get('bearer_token') or 
                   (twitter_config.get('api_key') and twitter_config.get('api_secret')))
    
    def _has_reddit_credentials(self) -> bool:
        """Check if Reddit credentials are available"""
        reddit_config = self.config.get('reddit', {})
        return bool(reddit_config.get('client_id') and reddit_config.get('client_secret'))
    
    def scan(self, sources: List[str] = None, save_history: bool = True) -> List[Dict[str, Any]]:
        """Perform a single scan for trending tickers"""
        if sources is None:
            sources = ['twitter', 'reddit']
        
        self.logger.info(f"Starting scan with sources: {sources}")
        
        all_posts = []
        
        # Fetch from Twitter
        if 'twitter' in sources and self.twitter_fetcher:
            try:
                twitter_posts = self.twitter_fetcher.get_standardized_posts()
                all_posts.extend(twitter_posts)
                self.logger.info(f"Fetched {len(twitter_posts)} Twitter posts")
            except Exception as e:
                self.logger.error(f"Error fetching Twitter data: {e}")
        
        # Fetch from Reddit
        if 'reddit' in sources and self.reddit_fetcher:
            try:
                reddit_posts = self.reddit_fetcher.get_standardized_posts()
                all_posts.extend(reddit_posts)
                self.logger.info(f"Fetched {len(reddit_posts)} Reddit posts")
            except Exception as e:
                self.logger.error(f"Error fetching Reddit data: {e}")
        
        if not all_posts:
            self.logger.warning("No posts fetched from any source")
            return []
        
        self.logger.info(f"Total posts collected: {len(all_posts)}")
        
        # Calculate hype scores
        try:
            results = self.hype_scorer.calculate_hype_scores(all_posts)
            self.logger.info(f"Generated hype scores for {len(results)} tickers")
            
            # Save to history if requested
            if save_history and results:
                for result in results:
                    history_entry = {
                        'timestamp': result['timestamp'],
                        'ticker': result['ticker'],
                        'mentions': result['mention_count'],
                        'sentiment_score': result['sentiment_score'],
                        'hype_score': result['hype_score'],
                        'rank': result['rank']
                    }
                    append_to_history(history_entry)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error calculating hype scores: {e}")
            return []

# CLI Context
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config-file', '-c', help='Path to configuration file')
@click.pass_context
def cli(ctx, verbose, config_file):
    """HypeFinder - Detect trending stocks and crypto on social media"""
    
    # Initialize context
    ctx.ensure_object(dict)
    
    # Update log level if verbose
    if verbose:
        config.config['output']['log_level'] = 'DEBUG'
    
    # Load additional config file if specified
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.config.update(file_config)
            click.echo(f"Loaded configuration from {config_file}")
        except Exception as e:
            click.echo(f"Error loading config file: {e}", err=True)
    
    # Validate credentials
    credentials_valid = config.validate_api_credentials()
    if not any(credentials_valid.values()):
        click.echo("Warning: No valid API credentials found. Please check your configuration.", err=True)
        click.echo("Copy env_template.txt to .env and fill in your API credentials.")

@cli.command()
@click.option('--sources', '-s', multiple=True, type=click.Choice(['twitter', 'reddit']), 
              default=['twitter', 'reddit'], help='Data sources to scan')
@click.option('--top', '-n', default=None, type=int, help='Number of top tickers to return')
@click.option('--output', '-o', type=click.Choice(['console', 'csv', 'both']), 
              default=None, help='Output format')
@click.option('--output-file', help='Output CSV file path')
@click.option('--min-mentions', type=int, help='Minimum mentions required')
@click.option('--explain', is_flag=True, help='Show detailed score explanations')
@click.pass_context
def scan(ctx, sources, top, output, output_file, min_mentions, explain):
    """Scan for trending tickers and generate hype scores"""
    
    # Update config with command line options
    if top:
        config.config['scoring']['top_n_tickers'] = top
    if min_mentions:
        config.config['scoring']['min_mentions'] = min_mentions
    if output:
        config.config['output']['format'] = output
    if output_file:
        config.config['output']['output_file'] = output_file
    
    try:
        # Initialize HypeFinder
        app = HypeFinder(config.config)
        
        # Perform scan
        results = app.scan(sources=list(sources))
        
        if not results:
            click.echo("No results found. Try adjusting your search parameters or check your API credentials.")
            return
        
        # Display results
        output_format = config.get('output.format', 'console')
        
        if output_format in ['console', 'both']:
            display_console_results(results, explain)
        
        if output_format in ['csv', 'both']:
            csv_file = config.get('output.output_file', 'hype_results.csv')
            save_results_to_csv(results, csv_file)
            click.echo(f"\nResults saved to {csv_file}")
        
        # Show summary
        summary = app.hype_scorer.get_scoring_summary(results)
        display_summary(summary)
        
    except Exception as e:
        click.echo(f"Error during scan: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--interval', '-i', default=60, type=int, help='Scan interval in minutes')
@click.option('--sources', '-s', multiple=True, type=click.Choice(['twitter', 'reddit']), 
              default=['twitter', 'reddit'], help='Data sources to scan')
@click.option('--duration', '-d', type=int, help='Duration to run in hours (default: run forever)')
@click.pass_context
def schedule(ctx, interval, sources, duration):
    """Run scheduled scans at regular intervals"""
    
    import schedule
    import time
    
    click.echo(f"Starting scheduled scans every {interval} minutes")
    if duration:
        click.echo(f"Will run for {duration} hours")
    
    try:
        app = HypeFinder(config.config)
        
        def run_scan():
            click.echo(f"\n{'='*50}")
            click.echo(f"Running scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"{'='*50}")
            
            results = app.scan(sources=list(sources))
            
            if results:
                # Always save to CSV for scheduled runs
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_file = f"hype_results_{timestamp}.csv"
                save_results_to_csv(results, csv_file)
                
                # Show top 5 results
                click.echo(f"\nTop 5 results:")
                for i, result in enumerate(results[:5], 1):
                    click.echo(f"  {i}. ${result['ticker']}: {result['hype_score']:.3f} "
                              f"({result['mention_count']} mentions)")
                
                click.echo(f"Full results saved to {csv_file}")
            else:
                click.echo("No results found in this scan")
        
        # Schedule the scan
        schedule.every(interval).minutes.do(run_scan)
        
        # Run initial scan
        run_scan()
        
        start_time = datetime.now()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
            
            # Check duration limit
            if duration:
                elapsed_hours = (datetime.now() - start_time).total_seconds() / 3600
                if elapsed_hours >= duration:
                    click.echo(f"\nReached duration limit of {duration} hours. Stopping.")
                    break
    
    except KeyboardInterrupt:
        click.echo("\nScheduled scanning stopped by user")
    except Exception as e:
        click.echo(f"Error in scheduled mode: {e}", err=True)

@cli.command()
@click.option('--show-credentials', is_flag=True, help='Show credential validation status')
@click.pass_context
def status(ctx, show_credentials):
    """Show HypeFinder configuration and status"""
    
    click.echo("HypeFinder Status")
    click.echo("=" * 50)
    
    # Configuration summary
    click.echo(f"Volume Weight: {config.get('scoring.volume_weight', 0.7)}")
    click.echo(f"Sentiment Weight: {config.get('scoring.sentiment_weight', 0.3)}")
    click.echo(f"Top N Tickers: {config.get('scoring.top_n_tickers', 20)}")
    click.echo(f"Min Mentions: {config.get('scoring.min_mentions', 5)}")
    click.echo(f"Output Format: {config.get('output.format', 'console')}")
    
    if show_credentials:
        click.echo("\nAPI Credentials Status:")
        credentials = config.validate_api_credentials()
        for service, valid in credentials.items():
            status = "✓ Valid" if valid else "✗ Missing/Invalid"
            click.echo(f"  {service.title()}: {status}")
    
    # Test component initialization
    click.echo("\nComponent Status:")
    try:
        app = HypeFinder(config.config)
        
        click.echo(f"  Twitter Fetcher: {'✓ Ready' if app.twitter_fetcher else '✗ Disabled'}")
        click.echo(f"  Reddit Fetcher: {'✓ Ready' if app.reddit_fetcher else '✗ Disabled'}")
        click.echo(f"  Hype Scorer: {'✓ Ready' if app.hype_scorer else '✗ Error'}")
        
    except Exception as e:
        click.echo(f"  Error initializing components: {e}")

@cli.command()
@click.option('--create-tickers', is_flag=True, help='Create sample ticker list file')
@click.option('--create-env', is_flag=True, help='Create sample .env file')
@click.pass_context
def setup(ctx, create_tickers, create_env):
    """Setup HypeFinder configuration files"""
    
    if create_tickers:
        create_sample_ticker_file()
        click.echo("Created sample tickers.csv file")
    
    if create_env:
        import shutil
        if os.path.exists('env_template.txt'):
            shutil.copy('env_template.txt', '.env')
            click.echo("Created .env file from template")
            click.echo("Please edit .env file and add your API credentials")
        else:
            click.echo("Error: env_template.txt not found")
    
    if not create_tickers and not create_env:
        click.echo("Setup options:")
        click.echo("  --create-tickers: Create sample ticker list")
        click.echo("  --create-env: Create .env configuration file")
        click.echo("\nFor API credentials, you'll need:")
        click.echo("  • Twitter Bearer Token (apply at developer.twitter.com)")
        click.echo("  • Reddit Client ID & Secret (create app at reddit.com/prefs/apps)")

def display_console_results(results: List[Dict[str, Any]], explain: bool = False):
    """Display results to console in formatted table"""
    if not results:
        return
    
    click.echo(f"\n🔥 Top {len(results)} Trending Tickers")
    click.echo("=" * 80)
    
    # Header
    header = f"{'Rank':<4} {'Ticker':<8} {'Hype':<8} {'Volume':<8} {'Sentiment':<10} {'Mentions':<8} {'Platforms':<12}"
    click.echo(header)
    click.echo("-" * 80)
    
    # Results
    for result in results:
        platforms_str = ','.join(result['platforms'])[:11]
        
        row = (f"{result['rank']:<4} "
               f"${result['ticker']:<7} "
               f"{result['hype_score']:<8.3f} "
               f"{result['volume_score']:<8.3f} "
               f"{result['sentiment_score']:<10.3f} "
               f"{result['mention_count']:<8} "
               f"{platforms_str:<12}")
        
        click.echo(row)
        
        # Show explanation if requested
        if explain and result['rank'] <= 3:  # Only explain top 3
            explanation = HypeScorer(config.config.get('scoring', {})).explain_score(
                result['ticker'], result
            )
            click.echo(f"\n{explanation}\n")

def display_summary(summary: Dict[str, Any]):
    """Display scan summary"""
    click.echo(f"\n📊 Scan Summary")
    click.echo("-" * 30)
    click.echo(f"Tickers analyzed: {summary['total_tickers']}")
    click.echo(f"Total mentions: {summary['total_mentions']}")
    click.echo(f"Average hype score: {summary['avg_hype_score']:.3f}")
    
    if summary.get('top_ticker'):
        click.echo(f"Top ticker: ${summary['top_ticker']} ({summary['top_hype_score']:.3f})")
    
    click.echo(f"Scan completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def save_results_to_csv(results: List[Dict[str, Any]], filename: str):
    """Save results to CSV file"""
    if not results:
        return
    
    # Flatten results for CSV
    csv_data = []
    for result in results:
        csv_row = {
            'rank': result['rank'],
            'ticker': result['ticker'],
            'hype_score': round(result['hype_score'], 4),
            'volume_score': round(result['volume_score'], 4),
            'sentiment_score': round(result['sentiment_score'], 4),
            'sentiment_confidence': round(result['sentiment_confidence'], 4),
            'mention_count': result['mention_count'],
            'platforms': ','.join(result['platforms']),
            'platform_count': result['platform_count'],
            'sentiment_trend': result['sentiment_trend'],
            'timestamp': result['timestamp']
        }
        csv_data.append(csv_row)
    
    save_to_csv(csv_data, filename)

def main():
    """Main entry point"""
    try:
        cli()
    except Exception as e:
        click.echo(f"Fatal error: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 