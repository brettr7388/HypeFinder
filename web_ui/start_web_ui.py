#!/usr/bin/env python3
"""
HypeFinder Web UI Startup Script
Simple script to start the web interface
"""

import os
import sys
import subprocess

def main():
    print("🌐 HypeFinder Web UI")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('server.py'):
        print("❌ Error: server.py not found!")
        print("Please run this script from the web_ui directory")
        sys.exit(1)
    
    # Check if Flask is installed
    try:
        import flask
        print("✅ Flask is installed")
    except ImportError:
        print("❌ Flask not found. Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask', 'flask-cors'])
    
    print("\n🚀 Starting HypeFinder Web Server...")
    print("📱 Open your browser to: http://localhost:8080")
    print("🔧 API endpoints available at: http://localhost:8080/api/")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    # Start the server
    subprocess.run([sys.executable, 'server.py'])

if __name__ == '__main__':
    main() 