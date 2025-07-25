# HypeFinder Web UI

A beautiful, modern web interface for HypeFinder that allows you to run scans and view results through your browser.

## Features

- 🎨 **Modern UI**: Clean, responsive design with gradient backgrounds and smooth animations
- 📊 **Real-time Results**: View trending tickers in a beautiful table format
- ⚙️ **Configurable Scans**: Adjust sources, top N tickers, minimum mentions, and output format
- 📈 **Visual Indicators**: Color-coded hype scores and sentiment analysis
- 📱 **Mobile Friendly**: Responsive design that works on all devices
- 🔄 **Live Status**: Real-time system status and API connectivity

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
cd web_ui
python3 start_web_ui.py
```

### Option 2: Manual Start

```bash
cd web_ui
pip3 install flask flask-cors
python3 server.py
```

### Option 3: Using Live Server (Static Mode)

If you prefer to use Live Server for the frontend only:

1. Install the Live Server extension in VS Code
2. Right-click on `index.html` and select "Open with Live Server"
3. Note: API calls will not work in this mode, but you can see the UI

## Usage

1. **Open your browser** to `http://localhost:8080`
2. **Configure your scan**:
   - Select data sources (Twitter, Reddit, or both)
   - Set the number of top tickers to return
   - Adjust minimum mentions threshold
   - Choose output format
3. **Click "Start Scan"** to run HypeFinder
4. **View results** in the beautiful table below

## API Endpoints

The web UI communicates with HypeFinder through these REST API endpoints:

- `GET /api/status` - Get system and API status
- `POST /api/scan` - Run a HypeFinder scan
- `GET /api/config` - Get current configuration

## Features Explained

### Hype Score Colors
- 🟢 **Green (High)**: Hype score ≥ 1.0
- 🟡 **Orange (Medium)**: Hype score 0.5-0.99
- 🔴 **Red (Low)**: Hype score < 0.5

### Sentiment Colors
- 🟢 **Green**: Positive sentiment (> 0.1)
- 🔴 **Red**: Negative sentiment (< -0.1)
- ⚪ **Gray**: Neutral sentiment (-0.1 to 0.1)

### Summary Cards
- **Tickers Analyzed**: Total number of tickers found
- **Total Mentions**: Combined mentions across all platforms
- **Average Hype Score**: Mean hype score of all tickers
- **Top Ticker**: Highest-scoring ticker with its score

## Troubleshooting

### "Flask not found" Error
```bash
pip3 install flask flask-cors
```

### "Port 8080 already in use" Error
The server will automatically try to find an available port, or you can modify `server.py` to use a different port.

### API Connection Errors
Make sure HypeFinder is properly configured with valid API credentials in your `.env` file.

### No Results Showing
- Check that your API credentials are valid
- Try reducing the minimum mentions threshold
- Ensure the selected data sources are working

## Development

The web UI consists of:
- `index.html` - Main HTML file with embedded CSS and JavaScript
- `server.py` - Flask API server that interfaces with HypeFinder
- `start_web_ui.py` - Convenient startup script

To modify the UI:
- Edit `index.html` for frontend changes
- Edit `server.py` for API changes
- The UI uses vanilla JavaScript - no build process required!

## Browser Compatibility

- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers

## Security Notes

- The web server runs on localhost only
- No authentication is required (intended for local use)
- API credentials are not exposed to the frontend
- All API calls go through the backend server 