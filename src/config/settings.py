import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ========== PLATFORM SELECTION ==========
    # Enable/disable platforms (set to True to monitor that platform)
    ENABLE_REDDIT = True
    ENABLE_YOUTUBE = True  # Set to True when you have API key
    ENABLE_MASTODON = True  # Set to True when you have credentials

    # ========== REDDIT API (FREE!) ==========
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
    REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
    REDDIT_USER_AGENT = "SocialMediaBot/1.0"

    # ========== YOUTUBE API (FREE with quota limits) ==========
    # Get API key from: https://console.cloud.google.com/
    # Enable YouTube Data API v3 for your project
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
    YOUTUBE_KEYWORDS = ['Draesontel']  # Keywords to search in YouTube videos/comments
    YOUTUBE_CHANNEL_NAME = os.getenv('YOUTUBE_CHANNEL_NAME', '')  # Your channel name (optional)

    # ========== MASTODON API (FREE and open source) ==========
    # Register your app at: https://mastodon.social/settings/applications
    # Or any other Mastodon instance
    MASTODON_INSTANCE_URL = os.getenv('MASTODON_INSTANCE_URL', 'https://mastodon.social')
    MASTODON_ACCESS_TOKEN = os.getenv('MASTODON_ACCESS_TOKEN', '')
    MASTODON_KEYWORDS = ['Draesontel']  # Keywords/hashtags to monitor

    # ========== AI/ML SETTINGS ==========
    # Ollama settings
    OLLAMA_MODEL = "llama3.2:3b"
    OLLAMA_HOST = "http://localhost:11434"

    # Hugging Face model settings
    HF_INTENT_MODEL = "facebook/bart-large-mnli"
    HF_SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
    HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    # Intent categories
    INTENT_LABELS = [
        "pricing and costs",
        "technical support issue",
        "positive feedback",
        "complaint or negative feedback",
        "feature request",
        "general question",
        "spam or irrelevant",
        "question about availability"
    ]

    # ========== GENERAL MONITORING SETTINGS ==========
    # Default keywords to monitor (used by Reddit and as fallback)
    MONITOR_KEYWORDS = [
        'Draesontel'  # my product
    ]

    # Confidence thresholds
    CANNED_RESPONSE_THRESHOLD = 0.75
    SENTIMENT_THRESHOLD = 0.8

    # Response constraints
    MAX_RESPONSE_LENGTH = 280
    MIN_RESPONSE_LENGTH = 20

    # Interactive mode (ask before posting)
    INTERACTIVE_MODE = True  # Set to False for fully automated posting