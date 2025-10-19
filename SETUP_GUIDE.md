# Multi-Platform Social Media Agent - Setup Guide

This guide will help you set up and configure the multi-platform social media monitoring agent.

## Table of Contents
1. [Installation](#installation)
2. [Platform Setup](#platform-setup)
   - [Reddit (Already Configured)](#reddit)
   - [YouTube](#youtube)
   - [Mastodon](#mastodon)
3. [Configuration](#configuration)
4. [Running the Agent](#running-the-agent)

---

## Installation

### 1. Install Dependencies

From the project root directory:

```bash
cd C:\Users\kaden\social-media-agent
pip install -r requirements.txt
```

### 2. Set up Ollama (if not already installed)

Download and install Ollama from https://ollama.ai

Then pull the model:
```bash
ollama pull llama3.2:3b
```

---

## Platform Setup

### Reddit (Already Configured ✅)

You already have Reddit set up! Your credentials are in `.env`:
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USERNAME`
- `REDDIT_PASSWORD`

---

### YouTube (FREE - Recommended)

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select existing project
3. Name it something like "Social Media Agent"

#### Step 2: Enable YouTube Data API v3
1. In the console, go to **APIs & Services > Library**
2. Search for "YouTube Data API v3"
3. Click on it and press **Enable**

#### Step 3: Create API Key
1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > API Key**
3. Copy the API key

#### Step 4: Add to .env file
Add this line to your `.env` file:
```
YOUTUBE_API_KEY=your_api_key_here
```

#### Step 5: Enable in config
Edit `src/config/settings.py`:
```python
ENABLE_YOUTUBE = True  # Change from False to True
```

**Quota Limits:**
- Free tier: 10,000 units/day
- Reading comments costs 1 unit each
- Searching costs 100 units
- Plenty for testing and demos!

**Note:** Replying requires OAuth 2.0 (more complex setup). For now, the agent will detect comments but print replies instead of posting them.

---

### Mastodon (FREE & Easy - Recommended)

#### Step 1: Create Mastodon Account
1. Go to [mastodon.social](https://mastodon.social) or any other Mastodon instance
2. Create a free account

#### Step 2: Register Your App
1. Go to **Preferences > Development > New Application**
2. Fill in:
   - **Application name:** "Social Media Monitor" (or anything)
   - **Scopes:** Check `read` and `write`
3. Click **Submit**

#### Step 3: Get Access Token
1. Click on your newly created application
2. Copy the **Your access token**

#### Step 4: Add to .env file
Add these lines to your `.env` file:
```
MASTODON_INSTANCE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_access_token_here
```

#### Step 5: Enable in config
Edit `src/config/settings.py`:
```python
ENABLE_MASTODON = True  # Change from False to True
```

**Benefits:**
- Completely free, no quota limits
- Can post AND read
- Great for demos and testing
- Open source and decentralized

---

## Configuration

### Edit Keywords to Monitor

Edit `src/config/settings.py`:

```python
# General keywords (used by all platforms)
MONITOR_KEYWORDS = [
    'YourBrandName',
    'YourProduct',
    'YourCompany'
]

# Platform-specific keywords (optional)
YOUTUBE_KEYWORDS = ['YourBrand', 'product review']
MASTODON_KEYWORDS = ['#YourBrand', '#YourProduct']
```

### Enable/Disable Platforms

In `src/config/settings.py`:

```python
ENABLE_REDDIT = True      # Currently working
ENABLE_YOUTUBE = False    # Set to True when you have API key
ENABLE_MASTODON = False   # Set to True when you have credentials
```

### Interactive Mode

Control whether the bot asks before posting:

```python
INTERACTIVE_MODE = True   # Ask before posting each reply
INTERACTIVE_MODE = False  # Fully automated (be careful!)
```

---

## Running the Agent

### From the src directory:

```powershell
cd C:\Users\kaden\social-media-agent\src
python main.py
```

### What You'll See:

```
🔧 INITIALIZING PLATFORM MONITORS
============================================================
✅ Connected to Reddit as u/YourUsername
✅ Connected to YouTube Data API
✅ Connected to Mastodon as @YourUsername@mastodon.social
============================================================
✅ 3 platform(s) initialized successfully
============================================================

🤖 MULTI-PLATFORM SOCIAL MEDIA AGENT STARTED!
   Active Platforms: Reddit, Youtube, Mastodon
   AI: Ollama + Hugging Face
   Keywords: ['YourBrand']

   Press Ctrl+C to stop
============================================================
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'google'"
Run: `pip install google-api-python-client`

### "ModuleNotFoundError: No module named 'mastodon'"
Run: `pip install Mastodon.py`

### "Database path not found"
Make sure you're running from the `src/` directory:
```bash
cd src
python main.py
```

### YouTube quota exceeded
- You've hit the daily limit (10,000 units)
- Wait until tomorrow (resets at midnight Pacific Time)
- Or reduce the number of videos searched

### Mastodon "401 Unauthorized"
- Check that your access token is correct in `.env`
- Make sure there are no extra spaces
- Verify the instance URL is correct

---

## Quick Start Recommendations

### For Testing (Fastest Setup):
1. ✅ Keep Reddit enabled (already working)
2. ✅ Add Mastodon (takes 5 minutes to set up)
3. Run with just these two platforms

### For Production Demo:
1. ✅ Enable all three: Reddit + YouTube + Mastodon
2. Set `INTERACTIVE_MODE = False` for automation
3. Monitor your brand keywords 24/7

### Cost Summary:
- **Reddit:** FREE ✅
- **YouTube:** FREE (with quota limits) ✅
- **Mastodon:** FREE (no limits!) ✅
- **Total Cost:** $0.00 ✅

---

## Next Steps

Once you have multiple platforms running:

1. Monitor the stats to see which platform gets the most engagement
2. Tune your keywords for each platform
3. Adjust the AI response thresholds in `config/settings.py`
4. Add more canned responses to the database for common questions

Need help? Check the code comments or create an issue!
