#!/usr/bin/env python3
"""
HypeFinder Web UI Startup Script
Handles port conflicts and provides better user experience
"""

import os
import sys
import socket
import subprocess
import time
from pathlib import Path

def find_free_port(start_port=8081, max_attempts=10):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_cors
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please install required packages:")
        print("   pip install flask flask-cors pandas")
        return False

def main():
    print("🚀 HypeFinder Web UI Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Find a free port
    port = find_free_port()
    if not port:
        print("❌ Could not find a free port")
        sys.exit(1)
    
    # Update server.py with the new port
    server_file = Path(__file__).parent / "server.py"
    if server_file.exists():
        with open(server_file, 'r') as f:
            content = f.read()
        
        # Update port in the file
        content = content.replace('port=8081', f'port={port}')
        content = content.replace('http://localhost:8081', f'http://localhost:{port}')
        
        with open(server_file, 'w') as f:
            f.write(content)
    
    print(f"🌐 Starting server on port {port}")
    print(f"📱 Open your browser to: http://localhost:{port}")
    print(f"🔧 API endpoints available at: http://localhost:{port}/api/")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "server.py"
        ], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 