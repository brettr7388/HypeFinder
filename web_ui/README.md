# HypeFinder Web UI

A modern, responsive web interface for HypeFinder - AI-powered trending tickers detection from social media.

## Features

- 🎨 **Modern Dark Theme UI** - Beautiful, responsive design with dark mode
- 📊 **Real-time Progress Tracking** - Visual progress bar during scans
- 🔧 **Flexible Configuration** - Easy-to-use filters and settings
- 📱 **Mobile Responsive** - Works perfectly on desktop and mobile devices
- 🚀 **Fast & Efficient** - Optimized for performance
- 📈 **Rich Data Visualization** - Card-based ticker display with detailed metrics

## Quick Start

### Prerequisites

Make sure you have the required Python packages installed:

```bash
pip install flask flask-cors pandas
```

### Starting the Web UI

1. **From the project root:**
   ```bash
   python web_ui/start_web_ui.py
   ```

2. **Or from the web_ui directory:**
   ```bash
   cd web_ui
   python start_web_ui.py
   ```

3. **Open your browser** to the URL shown in the terminal (typically `http://localhost:8081`)

## Usage

### Configuration Panel

The sidebar contains all configuration options:

- **Data Sources**: Select which platforms to scan (Twitter, Reddit)
- **Top N Tickers**: Number of trending tickers to return (1-50)
- **Minimum Mentions**: Filter tickers by minimum mention count
- **Output Format**: Choose console, CSV, or both output formats

### Dashboard

The main dashboard shows:

- **System Status**: Real-time status of API connections
- **Progress Tracking**: Visual progress bar during scans
- **Results Display**: Beautiful card-based ticker results
- **Summary Statistics**: Key metrics and insights

### Running a Scan

1. Configure your desired settings in the sidebar
2. Click "Start Scan" to begin the analysis
3. Watch the progress bar as the system:
   - Fetches data from selected sources
   - Analyzes ticker mentions and sentiment
   - Calculates hype scores
   - Displays results

### Understanding Results

Each ticker card shows:

- **Rank**: Position in trending list
- **Ticker Symbol**: Stock/crypto symbol
- **Hype Score**: Overall trending score (color-coded)
- **Volume Score**: Activity level metric
- **Sentiment Score**: Positive/negative sentiment
- **Mentions**: Total mention count
- **Platforms**: Sources where ticker was found

## API Endpoints

The web UI provides several REST API endpoints:

- `GET /api/health` - Health check
- `GET /api/status` - System and API status
- `GET /api/config` - Current configuration
- `GET /api/history` - Scan history
- `POST /api/scan` - Run a new scan

## Troubleshooting

### Port Already in Use

The startup script automatically finds an available port. If you see port conflicts:

1. Stop any existing servers
2. Restart the web UI
3. The script will automatically use the next available port

### API Connection Issues

If you see "Error" status for Twitter or Reddit:

1. Check your API credentials in the `.env` file
2. Ensure your API keys are valid and have proper permissions
3. Verify internet connectivity

### No Results Found

If scans return no results:

1. Check your API credentials
2. Try reducing the "Minimum Mentions" filter
3. Ensure your data sources are properly configured
4. Check the console output for detailed error messages

## Development

### File Structure

```
web_ui/
├── index.html          # Main UI interface
├── server.py           # Flask API server
├── start_web_ui.py     # Startup script
└── README.md           # This file
```

### Customization

The UI is built with vanilla HTML, CSS, and JavaScript. Key files to modify:

- `index.html` - Main interface and styling
- `server.py` - API endpoints and backend logic
- CSS variables in `index.html` - Theme colors and styling

### Adding New Features

1. **Frontend**: Add new UI elements to `index.html`
2. **Backend**: Add new API endpoints to `server.py`
3. **Integration**: Connect frontend to backend via JavaScript

## Browser Compatibility

- ✅ Chrome/Chromium (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ❌ Internet Explorer (not supported)

## License

This web UI is part of the HypeFinder project and follows the same license terms. 