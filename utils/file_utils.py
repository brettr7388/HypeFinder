import csv
import pandas as pd
from typing import List, Dict, Any, Optional
import os

def save_to_csv(data: List[Dict[str, Any]], filename: str, fieldnames: Optional[List[str]] = None) -> None:
    """Save list of dictionaries to CSV file"""
    if not data:
        return
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_ticker_list(filename: str = 'tickers.csv') -> List[str]:
    """Load known ticker symbols from CSV file"""
    tickers = []
    
    if not os.path.exists(filename):
        # Return some common tickers if file doesn't exist
        return ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'AMD', 'SPY', 'QQQ']
    
    try:
        df = pd.read_csv(filename)
        # Assume first column contains ticker symbols
        tickers = df.iloc[:, 0].str.upper().tolist()
    except Exception as e:
        print(f"Error loading ticker list: {e}")
        return []
    
    return tickers

def create_sample_ticker_file(filename: str = 'tickers.csv') -> None:
    """Create a sample ticker file with common stocks and crypto symbols"""
    sample_tickers = [
        'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'AMD', 'SPY', 'QQQ',
        'GME', 'AMC', 'BB', 'NOK', 'PLTR', 'WISH', 'CLOV', 'MVIS', 'SNDL', 'RKT',
        'BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'LTC', 'XRP', 'BCH', 'BNB', 'SOL',
        'DOGE', 'SHIB', 'SAFEMOON', 'PEPE', 'FLOKI', 'ELON', 'BABYDOGE'
    ]
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ticker'])
        for ticker in sample_tickers:
            writer.writerow([ticker])

def append_to_history(data: Dict[str, Any], filename: str = 'hype_history.csv') -> None:
    """Append hype results to historical data file"""
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'ticker', 'mentions', 'sentiment_score', 'hype_score', 'rank']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(data) 