#!/usr/bin/env python3
"""
HypeFinder Web API Server
Provides REST API endpoints for the web UI
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add the parent directory to the path to import HypeFinder modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Serve static files from the web_ui directory
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/api/status')
def api_status():
    """Get system status and API credentials status"""
    try:
        # Run the status command
        result = subprocess.run(
            ['python3', 'main.py', 'status', '--show-credentials'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        # Parse the output to extract status information
        output = result.stdout
        
        status = {
            'twitter': 'Unknown',
            'reddit': 'Unknown',
            'system': 'Ready'
        }
        
        # Look for status indicators in the output
        if 'Twitter: ✓ Valid' in output:
            status['twitter'] = 'Valid'
        elif 'Twitter API authentication failed' in output:
            status['twitter'] = 'Error'
            
        if 'Reddit: ✓ Valid' in output:
            status['reddit'] = 'Valid'
        elif 'Reddit API authentication failed' in output:
            status['reddit'] = 'Error'
            
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'twitter': 'Error',
            'reddit': 'Error',
            'system': 'Error'
        }), 500

@app.route('/api/scan', methods=['POST'])
def api_scan():
    """Run a HypeFinder scan with the provided parameters"""
    try:
        data = request.get_json()
        
        # Extract parameters
        sources = data.get('sources', ['reddit'])
        top_n = data.get('topN', 10)
        min_mentions = data.get('minMentions', 1)
        output_format = data.get('outputFormat', 'console')
        
        # Build the command
        cmd = ['python3', 'main.py', 'scan']
        
        # Add sources
        for source in sources:
            cmd.extend(['--sources', source])
        
        # Add other parameters
        cmd.extend([
            '--top', str(top_n),
            '--min-mentions', str(min_mentions),
            '--output', output_format
        ])
        
        # Run the scan
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Scan failed: {result.stderr}'
            }), 500
        
        # Parse the output to extract results
        output = result.stdout
        
        # Extract ticker data from the output
        tickers = []
        summary = {}
        
        # Look for the ticker table in the output
        lines = output.split('\n')
        in_table = False
        
        for line in lines:
            line = line.strip()
            
            # Look for table start
            if '🔥 Top' in line and 'Trending Tickers' in line:
                in_table = True
                continue
                
            # Look for table end
            if '📊 Scan Summary' in line:
                in_table = False
                break
                
            # Parse table rows - look for lines with pipe separators and numbers
            if in_table and '|' in line and not line.startswith('=') and not line.startswith('Rank') and not line.startswith('--'):
                # Split by pipe and clean up
                parts = [p.strip() for p in line.split('|') if p.strip()]
                
                # Debug: print the parts we're trying to parse
                print(f"Parsing line: {line}")
                print(f"Parts: {parts}")
                
                if len(parts) >= 7:
                    try:
                        # Clean up the ticker name (remove any extra spaces)
                        ticker_name = parts[1].strip()
                        
                        ticker_data = {
                            'rank': int(parts[0]),
                            'ticker': ticker_name,
                            'hype_score': float(parts[2]),
                            'volume_score': float(parts[3]),
                            'sentiment_score': float(parts[4]),
                            'mentions': int(parts[5]),
                            'platforms': [p.strip() for p in parts[6].split(',')]
                        }
                        tickers.append(ticker_data)
                        print(f"Successfully parsed ticker: {ticker_name}")
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing line: {line} - {e}")
                        continue
        
        # Extract summary information
        for line in lines:
            if 'Tickers analyzed:' in line:
                try:
                    summary['tickers_analyzed'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Total mentions:' in line:
                try:
                    summary['total_mentions'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Average hype score:' in line:
                try:
                    summary['average_hype_score'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif 'Top ticker:' in line:
                try:
                    summary['top_ticker'] = line.split(':')[1].strip()
                except:
                    pass
        
        # Debug: Print what we found
        print(f"Found {len(tickers)} tickers in output")
        print(f"Raw output length: {len(output)}")
        
        # If no tickers found but we have summary data, try a different parsing approach
        if len(tickers) == 0 and summary:
            print("No tickers parsed, trying alternative parsing...")
            # Try to extract from the raw output more aggressively
            lines = output.split('\n')
            for line in lines:
                if '|' in line and not line.startswith('=') and not line.startswith('Rank') and not line.startswith('--'):
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 7:
                        try:
                            ticker_data = {
                                'rank': int(parts[0]),
                                'ticker': parts[1].strip(),
                                'hype_score': float(parts[2]),
                                'volume_score': float(parts[3]),
                                'sentiment_score': float(parts[4]),
                                'mentions': int(parts[5]),
                                'platforms': [p.strip() for p in parts[6].split(',')]
                            }
                            tickers.append(ticker_data)
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing line: {line} - {e}")
                            continue
        
        return jsonify({
            'success': True,
            'data': {
                'tickers': tickers,
                'summary': summary,
                'raw_output': output[:500] + "..." if len(output) > 500 else output  # Truncate for debugging
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config')
def api_config():
    """Get current configuration"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'volume_weight': config.get('scoring.volume_weight'),
                'sentiment_weight': config.get('scoring.sentiment_weight'),
                'top_n_tickers': config.get('scoring.top_n_tickers'),
                'min_mentions': config.get('scoring.min_mentions'),
                'output_format': config.get('output.output_format')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting HypeFinder Web Server...")
    print("📱 Open your browser to: http://localhost:8080")
    print("🔧 API endpoints available at: http://localhost:8080/api/")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=8080) 