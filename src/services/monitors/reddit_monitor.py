import praw
from typing import List, Dict
from services.monitors.base_monitor import BaseMonitor

class RedditMonitor(BaseMonitor):
    """
    Reddit platform monitor using PRAW (Python Reddit API Wrapper).
    Monitors Reddit for keyword mentions and replies to posts/comments.
    """

    def __init__(self, config, db, response_generator):
        super().__init__(config, db, response_generator)
        self.reddit = None

    def get_platform_name(self) -> str:
        return 'reddit'

    def authenticate(self) -> bool:
        """Authenticate with Reddit using PRAW."""
        try:
            self.reddit = praw.Reddit(
                client_id=self.config.REDDIT_CLIENT_ID,
                client_secret=self.config.REDDIT_CLIENT_SECRET,
                user_agent=self.config.REDDIT_USER_AGENT,
                username=self.config.REDDIT_USERNAME,
                password=self.config.REDDIT_PASSWORD
            )

            # Test connection
            username = self.reddit.user.me()
            print(f"✅ Connected to Reddit as u/{username}")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to Reddit: {e}")
            return False

    def get_monitor_keywords(self) -> List[str]:
        """Get Reddit-specific keywords from config."""
        return self.config.MONITOR_KEYWORDS

    def search_mentions(self, keywords: List[str]) -> List[Dict]:
        """
        Search Reddit for posts and comments containing keywords.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of mention dictionaries
        """
        if not self.reddit:
            raise Exception("Reddit not authenticated. Call authenticate() first.")

        mentions = []
        subreddit = self.reddit.subreddit('all')

        for keyword in keywords:
            try:
                # Search posts
                for submission in subreddit.search(keyword, limit=10):
                    full_text = f"{submission.title}. {submission.selftext}"

                    mentions.append({
                        'id': f"post_{submission.id}",
                        'author': str(submission.author),
                        'content': full_text,
                        'url': f"https://reddit.com{submission.permalink}",
                        'type': 'post',
                        'subreddit': str(submission.subreddit),
                        'title': submission.title,
                        '_raw_object': submission  # Store for reply functionality
                    })

                # Search comments
                for comment in subreddit.comments(limit=20):
                    if not any(kw.lower() in comment.body.lower() for kw in keywords):
                        continue

                    mentions.append({
                        'id': f"comment_{comment.id}",
                        'author': str(comment.author),
                        'content': comment.body,
                        'url': f"https://reddit.com{comment.permalink}",
                        'type': 'comment',
                        'subreddit': str(comment.subreddit),
                        '_raw_object': comment
                    })

            except Exception as e:
                print(f"Error searching Reddit for '{keyword}': {e}")

        return mentions

    def post_reply(self, post_id: str, reply_text: str) -> bool:
        """
        Post a reply to a Reddit post or comment.

        Args:
            post_id: The Reddit post/comment ID (format: "post_xxxxx" or "comment_xxxxx")
            reply_text: The text of the reply

        Returns:
            bool: True if successful
        """
        try:
            # Extract the actual Reddit ID
            reddit_id = post_id.split('_', 1)[1] if '_' in post_id else post_id

            # Determine if it's a post or comment and get the object
            if post_id.startswith('post_'):
                submission = self.reddit.submission(id=reddit_id)
                submission.reply(reply_text)
            elif post_id.startswith('comment_'):
                comment = self.reddit.comment(id=reddit_id)
                comment.reply(reply_text)
            else:
                print(f"Unknown post type: {post_id}")
                return False

            return True

        except Exception as e:
            print(f"Error posting reply to {post_id}: {e}")
            return False

    def _is_own_post(self, mention: Dict) -> bool:
        """Check if the mention is from the bot's own Reddit account."""
        return mention.get('author') == self.config.REDDIT_USERNAME
