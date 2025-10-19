import time
import schedule
from datetime import datetime
from models.database import Database
from services.response_generator import ResponseGenerator
from config.settings import Config
from services.monitors.reddit_monitor import RedditMonitor
from services.monitors.youtube_monitor import YouTubeMonitor
from services.monitors.mastodon_monitor import MastodonMonitor

class MultiPlatformSocialAgent:
    """
    Multi-platform social media monitoring and response agent.
    Supports Reddit, YouTube, Mastodon, and more.
    """

    def __init__(self):
        self.config = Config()
        self.db = Database()

        print("Initializing Response Generator (loading ML models)...")
        self.response_gen = ResponseGenerator(self.db)

        # Initialize enabled platform monitors
        self.monitors = []
        self._initialize_monitors()

        if not self.monitors:
            print("⚠️  No platforms enabled! Check your config/settings.py")
            print("    Set ENABLE_REDDIT, ENABLE_YOUTUBE, or ENABLE_MASTODON to True")

    def _initialize_monitors(self):
        """Initialize all enabled platform monitors."""
        print("\n" + "="*60)
        print("🔧 INITIALIZING PLATFORM MONITORS")
        print("="*60)

        # Reddit
        if self.config.ENABLE_REDDIT:
            try:
                reddit_monitor = RedditMonitor(self.config, self.db, self.response_gen)
                if reddit_monitor.authenticate():
                    self.monitors.append(reddit_monitor)
            except Exception as e:
                print(f"⚠️  Failed to initialize Reddit monitor: {e}")

        # YouTube
        if self.config.ENABLE_YOUTUBE:
            try:
                if not self.config.YOUTUBE_API_KEY:
                    print("⚠️  YouTube enabled but YOUTUBE_API_KEY not set in .env")
                else:
                    youtube_monitor = YouTubeMonitor(self.config, self.db, self.response_gen)
                    if youtube_monitor.authenticate():
                        self.monitors.append(youtube_monitor)
            except Exception as e:
                print(f"⚠️  Failed to initialize YouTube monitor: {e}")

        # Mastodon
        if self.config.ENABLE_MASTODON:
            try:
                if not self.config.MASTODON_ACCESS_TOKEN:
                    print("⚠️  Mastodon enabled but MASTODON_ACCESS_TOKEN not set in .env")
                else:
                    mastodon_monitor = MastodonMonitor(self.config, self.db, self.response_gen)
                    if mastodon_monitor.authenticate():
                        self.monitors.append(mastodon_monitor)
            except Exception as e:
                print(f"⚠️  Failed to initialize Mastodon monitor: {e}")

        print("="*60)
        print(f"✅ {len(self.monitors)} platform(s) initialized successfully")
        print("="*60 + "\n")

    def monitor_all_platforms(self):
        """Monitor all enabled platforms for mentions."""
        total_processed = 0

        for monitor in self.monitors:
            try:
                processed_count = monitor.process_mentions()
                total_processed += processed_count
            except Exception as e:
                print(f"❌ Error monitoring {monitor.platform_name}: {e}")

        # Print overall stats
        if total_processed > 0:
            self.print_stats()

        return total_processed

    def print_stats(self):
        """Print performance statistics across all platforms."""
        stats = self.db.get_stats()
        print(f"\n{'='*60}")
        print(f"📊 OVERALL STATS (ALL PLATFORMS):")
        print(f"   Total processed: {stats['total_processed']}")
        print(f"   Canned responses: {stats['canned_responses']}")
        print(f"   AI generated: {stats['ai_responses']}")
        print(f"   Avg confidence: {stats['avg_confidence']:.2f}")
        print(f"   Avg similarity: {stats['avg_similarity']:.2f}")
        print(f"{'='*60}\n")

    def run(self):
        """Run the agent with scheduling."""
        print("=" * 60)
        print("🤖 MULTI-PLATFORM SOCIAL MEDIA AGENT STARTED!")
        print(f"   Active Platforms: {', '.join([m.platform_name.title() for m in self.monitors])}")
        print("   AI: Ollama + Hugging Face")
        print(f"   Keywords: {self.config.MONITOR_KEYWORDS}")
        print("\n   Press Ctrl+C to stop")
        print("=" * 60)

        # Run immediately
        self.monitor_all_platforms()

        # Schedule to run every 10 minutes
        schedule.every(10).minutes.do(self.monitor_all_platforms)

        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                print("\n🛑 Stopping agent...")
                self.print_stats()
                print("✅ Agent stopped successfully!")
                break

if __name__ == "__main__":
    agent = MultiPlatformSocialAgent()
    agent.run()
