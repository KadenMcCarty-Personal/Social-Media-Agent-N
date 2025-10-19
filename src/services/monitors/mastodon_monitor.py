from typing import List, Dict
from mastodon import Mastodon, StreamListener
from services.monitors.base_monitor import BaseMonitor
import time

class MastodonMonitor(BaseMonitor):
    """
    Mastodon platform monitor using Mastodon.py.
    Monitors Mastodon for keyword mentions and hashtags, and replies to toots.
    """

    def __init__(self, config, db, response_generator):
        super().__init__(config, db, response_generator)
        self.mastodon = None
        self.account_info = None

    def get_platform_name(self) -> str:
        return 'mastodon'

    def authenticate(self) -> bool:
        """Authenticate with Mastodon instance."""
        try:
            self.mastodon = Mastodon(
                access_token=self.config.MASTODON_ACCESS_TOKEN,
                api_base_url=self.config.MASTODON_INSTANCE_URL
            )

            # Verify credentials
            self.account_info = self.mastodon.account_verify_credentials()
            username = self.account_info['username']
            instance = self.config.MASTODON_INSTANCE_URL
            print(f"✅ Connected to Mastodon as @{username}@{instance}")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to Mastodon: {e}")
            return False

    def get_monitor_keywords(self) -> List[str]:
        """Get Mastodon-specific keywords from config."""
        return self.config.MASTODON_KEYWORDS if hasattr(self.config, 'MASTODON_KEYWORDS') else self.config.MONITOR_KEYWORDS

    def search_mentions(self, keywords: List[str]) -> List[Dict]:
        """
        Search Mastodon for posts (toots) containing keywords.

        Args:
            keywords: List of keywords/hashtags to search for

        Returns:
            List of mention dictionaries
        """
        if not self.mastodon:
            raise Exception("Mastodon not authenticated. Call authenticate() first.")

        mentions = []

        for keyword in keywords:
            try:
                # Search for the keyword
                # Mastodon search returns: accounts, statuses (toots), hashtags
                search_results = self.mastodon.search_v2(
                    q=keyword,
                    resolve=True
                )

                # Process status results (toots)
                for status in search_results.get('statuses', []):
                    # Skip if it's a reblog (boost)
                    if status.get('reblog'):
                        continue

                    mentions.append({
                        'id': str(status['id']),
                        'author': status['account']['username'],
                        'author_full': f"@{status['account']['acct']}",
                        'content': self._strip_html(status['content']),
                        'url': status['url'],
                        'visibility': status['visibility'],
                        'created_at': status['created_at'],
                        'in_reply_to_id': status.get('in_reply_to_id'),
                        'type': 'toot'
                    })

            except Exception as e:
                print(f"Error searching Mastodon for '{keyword}': {e}")

        # Also check direct mentions/notifications
        try:
            notifications = self.mastodon.notifications(
                types=['mention']
            )

            for notif in notifications:
                status = notif['status']

                # Check if any keyword appears in the mention
                content_lower = self._strip_html(status['content']).lower()
                if not any(kw.lower() in content_lower for kw in keywords):
                    continue

                mentions.append({
                    'id': str(status['id']),
                    'author': status['account']['username'],
                    'author_full': f"@{status['account']['acct']}",
                    'content': self._strip_html(status['content']),
                    'url': status['url'],
                    'visibility': status['visibility'],
                    'created_at': status['created_at'],
                    'in_reply_to_id': status.get('in_reply_to_id'),
                    'type': 'mention'
                })

        except Exception as e:
            print(f"Error getting Mastodon notifications: {e}")

        return mentions

    def post_reply(self, status_id: str, reply_text: str) -> bool:
        """
        Post a reply to a Mastodon toot.

        Args:
            status_id: The Mastodon status (toot) ID
            reply_text: The text of the reply

        Returns:
            bool: True if successful
        """
        try:
            # Get the original status to reply to
            original_status = self.mastodon.status(status_id)

            # Reply to the toot
            # Include @mention of the original author
            author_mention = f"@{original_status['account']['acct']}"

            # Only add mention if not already in reply
            if author_mention not in reply_text:
                full_reply = f"{author_mention} {reply_text}"
            else:
                full_reply = reply_text

            # Post the reply
            self.mastodon.status_post(
                status=full_reply,
                in_reply_to_id=status_id,
                visibility=original_status['visibility']  # Match original visibility
            )

            return True

        except Exception as e:
            print(f"Error posting reply to Mastodon toot {status_id}: {e}")
            return False

    def _is_own_post(self, mention: Dict) -> bool:
        """Check if the mention is from the bot's own Mastodon account."""
        if not self.account_info:
            return False

        return mention.get('author') == self.account_info['username']

    def _strip_html(self, html_content: str) -> str:
        """
        Strip HTML tags from Mastodon content.
        Mastodon returns content as HTML.

        Args:
            html_content: HTML string

        Returns:
            Plain text string
        """
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html_content)
        # Decode HTML entities
        import html
        text = html.unescape(text)
        return text.strip()

    def stream_timeline(self, callback_function):
        """
        Stream the home timeline in real-time (advanced feature).
        This allows real-time monitoring instead of polling.

        Args:
            callback_function: Function to call when new toot arrives
        """
        class TimelineListener(StreamListener):
            def __init__(self, callback):
                self.callback = callback

            def on_update(self, status):
                """Called when a new toot appears in timeline."""
                self.callback(status)

        listener = TimelineListener(callback_function)
        self.mastodon.stream_user(listener, run_async=False, reconnect_async=False)
