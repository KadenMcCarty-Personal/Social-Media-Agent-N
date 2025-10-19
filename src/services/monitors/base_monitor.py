from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple

class BaseMonitor(ABC):
    """
    Abstract base class for all social media platform monitors.
    Each platform implementation must inherit from this class and implement all abstract methods.
    """

    def __init__(self, config, db, response_generator):
        """
        Initialize the monitor with shared dependencies.

        Args:
            config: Configuration object with platform-specific settings
            db: Database instance for tracking processed posts
            response_generator: ResponseGenerator instance for creating replies
        """
        self.config = config
        self.db = db
        self.response_gen = response_generator
        self.platform_name = self.get_platform_name()

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Return the platform name (e.g., 'reddit', 'youtube', 'mastodon').
        This is used for database tracking and logging.
        """
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform's API.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass

    @abstractmethod
    def search_mentions(self, keywords: List[str]) -> List[Dict]:
        """
        Search for posts/comments mentioning the given keywords.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of dictionaries containing post data with keys:
                - id: Unique post/comment ID
                - author: Username of the author
                - content: The post/comment text
                - url: URL to the post/comment (optional)
                - parent_id: ID of parent post if this is a reply (optional)
        """
        pass

    @abstractmethod
    def post_reply(self, post_id: str, reply_text: str) -> bool:
        """
        Post a reply to a specific post/comment.

        Args:
            post_id: The unique ID of the post to reply to
            reply_text: The text of the reply

        Returns:
            bool: True if reply posted successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_monitor_keywords(self) -> List[str]:
        """
        Get the list of keywords this monitor should search for.
        Platform-specific implementation to read from config.

        Returns:
            List of keywords to monitor
        """
        pass

    def process_mentions(self) -> int:
        """
        Main processing loop: search for mentions, generate responses, and reply.
        This is implemented in the base class but can be overridden if needed.

        Returns:
            int: Number of mentions processed
        """
        print(f"\n{'='*60}")
        print(f"🔍 Checking {self.platform_name.title()}... {self._get_timestamp()}")
        print(f"{'='*60}")

        processed_count = 0
        keywords = self.get_monitor_keywords()

        for keyword in keywords:
            print(f"\n🔎 Searching for: '{keyword}'")

            try:
                mentions = self.search_mentions([keyword])

                for mention in mentions:
                    post_id = f"{self.platform_name}_{mention['id']}"

                    # Skip if already processed
                    if self.db.is_processed(post_id):
                        continue

                    # Skip if it's your own post (if author info available)
                    if self._is_own_post(mention):
                        continue

                    print(f"\n📬 New {self.platform_name} post by {mention.get('author', 'Unknown')}")
                    print(f"   Content: {mention['content'][:100]}...")

                    # Generate response
                    response_data = self.response_gen.generate_response(mention['content'])

                    print(f"   💬 Response ({response_data['type']}): {response_data['text'][:80]}...")

                    # Post reply
                    try:
                        # Optional: Allow user to modify response
                        if self.config.INTERACTIVE_MODE if hasattr(self.config, 'INTERACTIVE_MODE') else False:
                            user_input = input("Modify this reply? (y/n/skip): ")
                            if user_input == "y":
                                response_data['text'] = input("Enter response: ")
                            elif user_input == "skip":
                                continue

                        success = self.post_reply(mention['id'], response_data['text'])

                        if success:
                            print("   ✅ Reply posted!")

                            self.db.mark_processed(
                                post_id,
                                self.platform_name,
                                mention['content'],
                                mention.get('author', 'Unknown'),
                                response_data['intent'],
                                response_data['sentiment'],
                                response_data['confidence'],
                                response_data['text'],
                                response_data['type'],
                                response_data['similarity_score']
                            )

                            processed_count += 1
                        else:
                            print("   ❌ Failed to post reply")

                    except Exception as e:
                        print(f"   ❌ Failed to post: {e}")
                        # Mark as processed to avoid retry loops
                        self.db.mark_processed(
                            post_id,
                            self.platform_name,
                            mention['content'],
                            mention.get('author', 'Unknown'),
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
            print(f"\nℹ️  No new mentions found on {self.platform_name}")
        else:
            print(f"\n✅ Processed {processed_count} new mentions on {self.platform_name}")

        return processed_count

    def _is_own_post(self, mention: Dict) -> bool:
        """
        Check if the mention is from the bot's own account.
        Override in platform-specific implementation if needed.

        Args:
            mention: The mention dictionary

        Returns:
            bool: True if this is the bot's own post
        """
        return False

    def _get_timestamp(self) -> str:
        """Get formatted current timestamp."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
