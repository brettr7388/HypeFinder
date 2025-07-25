#!/usr/bin/env python3
"""
HypeFinder - Main Entry Point
Identifies trending stocks and crypto on Twitter and Reddit
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cli.main import main

if __name__ == '__main__':
    main() 