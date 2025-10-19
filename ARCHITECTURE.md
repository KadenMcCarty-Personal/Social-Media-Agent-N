# Multi-Platform Social Media Agent - Architecture

## Project Structure

```
social-media-agent/
├── src/                                 # Main source code
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                 # Configuration for all platforms
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py                 # SQLite database operations
│   ├── services/
│   │   ├── monitors/                   # Platform-specific monitors
│   │   │   ├── __init__.py
│   │   │   ├── base_monitor.py        # Abstract base class
│   │   │   ├── reddit_monitor.py      # Reddit implementation
│   │   │   ├── youtube_monitor.py     # YouTube implementation
│   │   │   └── mastodon_monitor.py    # Mastodon implementation
│   │   ├── ml_models.py               # ML model management
│   │   ├── ollama_client.py           # Ollama API client
│   │   └── response_generator.py      # Response generation pipeline
│   ├── core/                           # Future: Core business logic
│   │   └── __init__.py
│   └── main.py                         # Application entry point
├── data/
│   └── social_agent.db                # SQLite database file
├── tests/
│   └── __init__.py
├── .env                                # Environment variables (not in git)
├── .gitignore
├── requirements.txt
├── SETUP_GUIDE.md
└── ARCHITECTURE.md (this file)
```

---

## Component Architecture

### 1. Platform Monitors (Strategy Pattern)

Each platform implements the `BaseMonitor` abstract class:

```python
BaseMonitor (ABC)
├── RedditMonitor
├── YouTubeMonitor
└── MastodonMonitor
```

**Common Interface:**
- `authenticate()` - Connect to platform API
- `search_mentions(keywords)` - Find posts mentioning keywords
- `post_reply(post_id, text)` - Reply to a post
- `process_mentions()` - Main processing loop

**Benefits:**
- Easy to add new platforms
- Consistent behavior across platforms
- Shared processing logic in base class

---

### 2. Response Generation Pipeline

```
User Post/Comment
      ↓
[Intent Classification] ← Hugging Face (BART)
      ↓
[Sentiment Analysis] ← Hugging Face (DistilBERT)
      ↓
[Semantic Search] ← Sentence Transformers
      ↓
Decision: Canned Response vs AI Generation
      ↓
If Canned → Use best matching template
If AI → Ollama (LLaMA) with context
      ↓
[Validation & Toxicity Check]
      ↓
Final Response
```

---

### 3. Database Schema

**processed_posts table:**
```sql
- id (PRIMARY KEY)
- post_id (UNIQUE)         # platform_type_id (e.g., "reddit_post_abc123")
- platform (TEXT)          # 'reddit', 'youtube', 'mastodon'
- content (TEXT)
- author (TEXT)
- intent (TEXT)
- sentiment (TEXT)
- confidence (REAL)
- processed_at (TIMESTAMP)
- response_sent (TEXT)
- response_type (TEXT)     # 'canned', 'ai', 'fallback'
- similarity_score (REAL)
```

**canned_responses table:**
```sql
- id (PRIMARY KEY)
- keyword (TEXT)
- response_template (TEXT)
- category (TEXT)
- intent (TEXT)
- embedding (BLOB)         # Vector embedding for semantic search
```

---

## Data Flow

### Monitoring Cycle:

```
1. main.py starts
   ↓
2. Initialize enabled platform monitors
   ↓
3. Each monitor authenticates with its API
   ↓
4. Every 10 minutes (scheduled):
   ↓
5. For each platform:
   - Search for keywords
   - Filter already processed posts
   - For each new mention:
     * Generate response using ResponseGenerator
     * Post reply (if interactive mode allows)
     * Save to database
   ↓
6. Print statistics
   ↓
7. Repeat
```

### Response Generation Flow:

```
Post Content
     ↓
[ML Models] - Classify intent & sentiment
     ↓
[Semantic Search] - Find similar canned responses
     ↓
[Decision Logic]
  ├─ High similarity (>0.75) → Use canned response
  └─ Low similarity → Generate with Ollama
       ↓
  [Ollama] - Generate contextual response
     ↓
[Validation] - Length, format, toxicity check
     ↓
Final Response
```

---

## Platform-Specific Details

### Reddit (PRAW)
- **Authentication:** Username/password + API credentials
- **Search:** Full-text search across all subreddits
- **Reply:** Direct API call to post reply
- **Rate Limits:** Very generous for personal use

### YouTube (Google API)
- **Authentication:** API key (read-only)
- **Search:** Search videos by keyword, then fetch comments
- **Reply:** Requires OAuth 2.0 (not implemented in v1)
- **Rate Limits:** 10,000 units/day (1 unit per comment read)

### Mastodon (Mastodon.py)
- **Authentication:** Access token
- **Search:** Keyword search + hashtag search + notifications
- **Reply:** Full posting capability
- **Rate Limits:** None (depends on instance)

---

## AI/ML Stack

### Models Used:

1. **Intent Classification**
   - Model: `facebook/bart-large-mnli`
   - Purpose: Classify user intent (support, pricing, complaint, etc.)
   - Type: Zero-shot classification

2. **Sentiment Analysis**
   - Model: `distilbert-base-uncased-finetuned-sst-2-english`
   - Purpose: Detect positive/negative sentiment
   - Type: Binary classification

3. **Semantic Search**
   - Model: `sentence-transformers/all-MiniLM-L6-v2`
   - Purpose: Find similar canned responses
   - Type: Sentence embeddings + cosine similarity

4. **Text Generation**
   - Model: `llama3.2:3b` (via Ollama)
   - Purpose: Generate contextual responses when no canned response fits
   - Type: Large language model

---

## Configuration Management

**Environment Variables (.env):**
- API keys and secrets
- Usernames and passwords
- Platform-specific tokens

**Config Class (settings.py):**
- Platform enable/disable flags
- Keywords to monitor
- ML model names
- Response thresholds
- Interactive mode settings

---

## Extension Points

### Adding a New Platform:

1. Create `src/services/monitors/platform_monitor.py`
2. Inherit from `BaseMonitor`
3. Implement required methods
4. Add config settings to `settings.py`
5. Add credentials to `.env`
6. Import and initialize in `main.py`

### Example:
```python
class TwitterMonitor(BaseMonitor):
    def get_platform_name(self):
        return 'twitter'

    def authenticate(self):
        # Twitter API auth logic
        pass

    def search_mentions(self, keywords):
        # Twitter search logic
        pass

    def post_reply(self, post_id, text):
        # Twitter reply logic
        pass
```

---

## Future Enhancements

### Potential Improvements:
1. **Web Dashboard** - Flask/React UI for monitoring
2. **OAuth for YouTube** - Enable posting replies
3. **Real-time Streaming** - Use Mastodon/Twitter streaming APIs
4. **Analytics Dashboard** - Visualize engagement metrics
5. **Multi-account Support** - Manage multiple brand accounts
6. **Webhook Integration** - Slack/Discord notifications
7. **A/B Testing** - Test different response strategies
8. **Custom ML Models** - Train on your specific brand data

---

## Performance Considerations

### Database:
- SQLite is fine for single-user, moderate volume
- For high volume, consider PostgreSQL

### ML Models:
- Models load once at startup (3-5 seconds)
- Inference is fast (~100-200ms per post)
- GPU acceleration optional (CUDA)

### API Rate Limits:
- Reddit: ~60 requests/minute (generous)
- YouTube: 10,000 units/day (manageable)
- Mastodon: No strict limits (instance-dependent)

### Scalability:
- Current: Single-threaded, polling-based
- Future: Multi-threaded or async for multiple platforms
- Cloud: Can deploy to AWS/GCP with minimal changes

---

## Security Best Practices

1. ✅ API keys in `.env` (not in code)
2. ✅ `.env` in `.gitignore` (not committed)
3. ✅ Toxicity checking before posting
4. ✅ Rate limit awareness
5. ⚠️ Consider: Input validation for user prompts
6. ⚠️ Consider: Logging sensitive operations
7. ⚠️ Consider: Encrypted storage for tokens

---

## Testing Strategy

### Current:
- Manual testing with live APIs
- Small keyword searches for safety

### Recommended:
1. Unit tests for each monitor
2. Mock API responses for testing
3. Integration tests with test accounts
4. Validation of response quality
5. Rate limit handling tests

---

This architecture is designed to be:
- ✅ Modular (easy to add platforms)
- ✅ Maintainable (clear separation of concerns)
- ✅ Extensible (base classes and interfaces)
- ✅ Cost-effective (all free APIs)
- ✅ Production-ready (with proper configuration)
