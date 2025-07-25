# HypeFinder Installation Guide

## Prerequisites

- Python 3.8 or higher
- Internet connection
- Twitter Developer Account (free)
- Reddit Account

## Step-by-Step Installation

### 1. Install Python Dependencies

```bash
# Install required packages
pip3 install -r requirements.txt

# On some systems, you might need:
pip install -r requirements.txt
```

### 2. Set Up API Credentials

#### Twitter API Setup
1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Apply for a developer account (usually approved instantly)
3. Create a new "App" in your developer portal
4. Generate a Bearer Token from the "Keys and Tokens" tab
5. Copy the Bearer Token for use in step 3

#### Reddit API Setup
1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Choose "script" as the application type
4. Fill in any name and description
5. Note the client ID (under the app name) and client secret

### 3. Configure Environment Variables

```bash
# Create configuration files
python3 main.py setup --create-env --create-tickers

# Edit the .env file with your credentials
nano .env  # or use any text editor
```

Add your credentials to the `.env` file:
```
TWITTER_BEARER_TOKEN=your_bearer_token_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
```

### 4. Test Installation

```bash
# Check that everything is working
python3 main.py status --show-credentials

# Run a quick test scan
python3 main.py scan --min-mentions 1 --top 5
```

## Common Installation Issues

### "ModuleNotFoundError"
Install missing dependencies:
```bash
pip3 install [missing_module_name]
```

### "python: command not found"
Use `python3` instead of `python`:
```bash
python3 main.py scan
```

### Twitter API Authentication Failed
- Double-check your Bearer Token
- Ensure no extra spaces in your .env file
- Verify your Twitter developer account is approved

### Reddit API Authentication Failed
- Verify client ID and secret are correct
- Make sure you selected "script" application type
- Check that your Reddit account is in good standing

### "No results found"
- Try lowering the minimum mentions: `--min-mentions 1`
- Check your internet connection
- Verify API credentials are working with the status command

## Verify Installation

If everything is working correctly, you should see output like:

```bash
$ python3 main.py status --show-credentials

HypeFinder Status
==================================================
Volume Weight: 0.7
Sentiment Weight: 0.3
Top N Tickers: 20
Min Mentions: 5
Output Format: console

API Credentials Status:
  Twitter: ✓ Valid
  Reddit: ✓ Valid

Component Status:
  Twitter Fetcher: ✓ Ready
  Reddit Fetcher: ✓ Ready
  Hype Scorer: ✓ Ready
```

## First Run

Once installed, try your first scan:

```bash
# Basic scan
python3 main.py scan

# Detailed scan with explanations
python3 main.py scan --explain --top 5

# Save results to CSV
python3 main.py scan --output both
```

## Troubleshooting

If you encounter issues:

1. **Check Python version**: `python3 --version` (should be 3.8+)
2. **Verify dependencies**: `pip3 show praw tweepy click`
3. **Test network**: `curl -I https://api.twitter.com`
4. **Check logs**: Use `--verbose` flag for detailed error messages

## Getting Help

- Check the main [README.md](README.md) for usage examples
- Use `python3 main.py --help` for command options
- Enable verbose logging: `python3 main.py --verbose scan`
- Test individual components with minimal settings

Enjoy using HypeFinder! 🚀 