import praw
import time
import schedule
from datetime import datetime
from models.database import Database
from services.response_generator import ResponseGenerator
from config.settings import Config

class SocialMediaAgent:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        
        print("Initializing Response Generator (loading ML models)...")
        self.response_gen = ResponseGenerator(self.db)
        
        # Initialize Reddit
        try:
            self.reddit = praw.Reddit(
                client_id=self.config.REDDIT_CLIENT_ID,
                client_secret=self.config.REDDIT_CLIENT_SECRET,
                user_agent=self.config.REDDIT_USER_AGENT,
                username=self.config.REDDIT_USERNAME,
                password=self.config.REDDIT_PASSWORD
            )
            
            # Test connection
            print(f"✅ Connected to Reddit as u/{self.reddit.user.me()}")
            
        except Exception as e:
            print(f"❌ Failed to connect to Reddit: {e}")
            raise
    
    def monitor_reddit_mentions(self):
        """Monitor Reddit for brand mentions"""
        print(f"\n{'='*60}")
        print(f"🔍 Checking Reddit... {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        processed_count = 0
        
        for keyword in self.config.MONITOR_KEYWORDS:
            print(f"\n🔎 Searching for: '{keyword}'")
            
            try:
                # Search across all of Reddit
                subreddit = self.reddit.subreddit('all')
                
                # Search posts
                for submission in subreddit.search(keyword):
                    post_id = f"reddit_post_{submission.id}"
                    
                    # Skip if already processed
                    if self.db.is_processed(post_id):
                        continue
                    
                    # Skip if it's your own post
                    if str(submission.author) == self.config.REDDIT_USERNAME:
                        continue
                    
                    print(f"\n📬 New post by u/{submission.author}")
                    print(f"   Subreddit: r/{submission.subreddit}")
                    print(f"   Title: {submission.title}\n")
                    print(f"   Post: {submission.selftext}\n")
                    
                    # Combine title and body
                    full_text = f"{submission.title}. {submission.selftext}"
                    
                    # if len(full_text.strip()) < 10:
                    #     print("   ⏭️  Skipping - too short")
                    #     continue
                    
                    # Generate response
                    response_data = self.response_gen.generate_response(full_text)
                    
                    print(f"   💬 Response ({response_data['type']}): {response_data['text']}...")
                    
                    # Post reply
                    try:
                        user_input = input("Would you like to modify this reply? (y/n): ")
                        if (user_input == "y"):
                            user_input = input("enter response to post: ")
                            submission.reply(user_input)
                        elif(user_input == "skip"):
                            continue
                        else:
                            submission.reply(response_data['text'])

                        print("   ✅ Reply posted!")
                        
                        self.db.mark_processed(
                            post_id, 'reddit', full_text, str(submission.author),
                            response_data['intent'],
                            response_data['sentiment'],
                            response_data['confidence'],
                            response_data['text'],
                            response_data['type'],
                            response_data['similarity_score']
                        )
                        
                        processed_count += 1
                        
                    except Exception as e:
                        print(f"   ❌ Failed to post: {e}")
                        # Mark as processed anyway to avoid retry loops
                        self.db.mark_processed(
                            post_id, 'reddit', full_text, str(submission.author),
                            response_data['intent'],
                            response_data['sentiment'],
                            response_data['confidence'],
                            f"FAILED: {str(e)}",
                            'failed',
                            response_data['similarity_score']
                        )
                
                # Also check comments mentioning your brand
                for comment in subreddit.comments(limit=20):
                    # Check if comment mentions any keyword
                    if not any(kw.lower() in comment.body.lower() for kw in self.config.MONITOR_KEYWORDS):
                        continue
                    
                    comment_id = f"reddit_comment_{comment.id}"
                    
                    if self.db.is_processed(comment_id):
                        continue
                    
                    # Skip your own comments
                    if str(comment.author) == self.config.REDDIT_USERNAME:
                        continue
                    
                    print(f"\n💬 New comment by u/{comment.author}")
                    print(f"   In: r/{comment.subreddit}")
                    print(f"   Text: {comment.body[:80]}...")
                    
                    # Generate response
                    response_data = self.response_gen.generate_response(comment.body)
                    
                    print(f"   💬 Response ({response_data['type']}): {response_data['text'][:80]}...")
                    
                    try:
                        comment.reply(response_data['text'])
                        print("   ✅ Reply posted!")
                        
                        self.db.mark_processed(
                            comment_id, 'reddit', comment.body, str(comment.author),
                            response_data['intent'],
                            response_data['sentiment'],
                            response_data['confidence'],
                            response_data['text'],
                            response_data['type'],
                            response_data['similarity_score']
                        )
                        
                        processed_count += 1
                        
                    except Exception as e:
                        print(f"   ❌ Failed to post: {e}")
                        self.db.mark_processed(
                            comment_id, 'reddit', comment.body, str(comment.author),
                            response_data['intent'],
                            response_data['sentiment'],
                            response_data['confidence'],
                            f"FAILED: {str(e)}",
                            'failed',
                            response_data['similarity_score']
                        )
                
            except Exception as e:
                print(f"❌ Error searching for '{keyword}': {e}")
        
        if processed_count == 0:
            print("\nℹ️  No new mentions found")
        else:
            print(f"\n✅ Processed {processed_count} new mentions")
        
        # Print stats
        self.print_stats()
    
    def print_stats(self):
        """Print performance statistics"""
        stats = self.db.get_stats()
        print(f"\n{'='*60}")
        print(f"📊 OVERALL STATS:")
        print(f"   Total processed: {stats['total_processed']}")
        print(f"   Canned responses: {stats['canned_responses']}")
        print(f"   AI generated: {stats['ai_responses']}")
        print(f"   Avg confidence: {stats['avg_confidence']:.2f}")
        print(f"   Avg similarity: {stats['avg_similarity']:.2f}")
        print(f"{'='*60}\n")
    
    def run(self):
        """Run the agent with scheduling"""
        print("=" * 60)
        print("🤖 SOCIAL MEDIA AGENT STARTED!")
        print("   Platform: Reddit")
        print("   AI: Ollama + Hugging Face")
        print(f"   Monitoring keywords: {self.config.MONITOR_KEYWORDS}")
        print("\n   Press Ctrl+C to stop")
        print("=" * 60)
        
        # Run immediately
        self.monitor_reddit_mentions()
        
        # Schedule to run every 10 minutes (Reddit allows this)
        schedule.every(10).minutes.do(self.monitor_reddit_mentions)
        
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
    agent = SocialMediaAgent()
    agent.run()