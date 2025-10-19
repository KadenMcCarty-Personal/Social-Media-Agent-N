import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Reddit API (FREE!)
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
    REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
    REDDIT_USER_AGENT = "SocialMediaBot/1.0"
    
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
    
    # Keywords to monitor (CHANGE THESE!)
    MONITOR_KEYWORDS = [
        'Draesontel' # my product
    ]
    
    # Confidence thresholds
    CANNED_RESPONSE_THRESHOLD = 0.75
    SENTIMENT_THRESHOLD = 0.8
    
    # Response constraints
    MAX_RESPONSE_LENGTH = 280
    MIN_RESPONSE_LENGTH = 20