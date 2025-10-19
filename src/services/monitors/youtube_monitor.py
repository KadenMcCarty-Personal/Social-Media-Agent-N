from typing import List, Dict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from services.monitors.base_monitor import BaseMonitor

class YouTubeMonitor(BaseMonitor):
    """
    YouTube platform monitor using YouTube Data API v3.
    Monitors comments on specified videos/channels for keywords and replies.
    """

    def __init__(self, config, db, response_generator):
        super().__init__(config, db, response_generator)
        self.youtube = None

    def get_platform_name(self) -> str:
        return 'youtube'

    def authenticate(self) -> bool:
        """Authenticate with YouTube Data API using API key."""
        try:
            self.youtube = build('youtube', 'v3', developerKey=self.config.YOUTUBE_API_KEY)
            print(f"✅ Connected to YouTube Data API")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to YouTube: {e}")
            return False

    def get_monitor_keywords(self) -> List[str]:
        """Get YouTube-specific keywords from config."""
        return self.config.YOUTUBE_KEYWORDS if hasattr(self.config, 'YOUTUBE_KEYWORDS') else self.config.MONITOR_KEYWORDS

    def search_mentions(self, keywords: List[str]) -> List[Dict]:
        """
        Search YouTube comments for keywords.

        Note: YouTube API doesn't support direct keyword search in comments.
        Instead, this searches for videos by keyword, then checks their comments.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of comment dictionaries
        """
        if not self.youtube:
            raise Exception("YouTube not authenticated. Call authenticate() first.")

        mentions = []

        for keyword in keywords:
            try:
                # First, search for videos related to the keyword
                video_search = self.youtube.search().list(
                    q=keyword,
                    part='id,snippet',
                    maxResults=5,  # Limit to save quota
                    type='video',
                    order='date'  # Get recent videos
                ).execute()

                # For each video, get comments
                for item in video_search.get('items', []):
                    video_id = item['id']['videoId']
                    video_title = item['snippet']['title']

                    # Get comments for this video
                    comments = self._get_video_comments(video_id, keyword)

                    for comment in comments:
                        mentions.append({
                            'id': comment['id'],
                            'author': comment['author'],
                            'content': comment['text'],
                            'url': f"https://www.youtube.com/watch?v={video_id}&lc={comment['id']}",
                            'video_id': video_id,
                            'video_title': video_title,
                            'parent_id': comment.get('parent_id'),
                            'type': 'comment'
                        })

            except HttpError as e:
                print(f"YouTube API error searching for '{keyword}': {e}")
            except Exception as e:
                print(f"Error searching YouTube for '{keyword}': {e}")

        return mentions

    def _get_video_comments(self, video_id: str, keyword: str = None, max_results: int = 20) -> List[Dict]:
        """
        Get comments from a specific video, optionally filtering by keyword.

        Args:
            video_id: YouTube video ID
            keyword: Optional keyword to filter comments
            max_results: Maximum number of comments to retrieve

        Returns:
            List of comment dictionaries
        """
        comments = []

        try:
            # Get top-level comments
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=max_results,
                textFormat='plainText',
                order='time'  # Get most recent first
            )

            response = request.execute()

            for item in response.get('items', []):
                top_comment = item['snippet']['topLevelComment']['snippet']
                comment_id = item['snippet']['topLevelComment']['id']
                comment_text = top_comment['textDisplay']

                # Filter by keyword if provided
                if keyword and keyword.lower() not in comment_text.lower():
                    continue

                comments.append({
                    'id': comment_id,
                    'author': top_comment['authorDisplayName'],
                    'text': comment_text,
                    'likes': top_comment.get('likeCount', 0),
                    'published_at': top_comment['publishedAt']
                })

                # Check replies to this comment
                if item['snippet']['totalReplyCount'] > 0:
                    replies = self._get_comment_replies(comment_id, keyword)
                    for reply in replies:
                        reply['parent_id'] = comment_id
                        comments.append(reply)

        except HttpError as e:
            # Comments might be disabled for the video
            if e.resp.status == 403:
                print(f"   ⚠️ Comments disabled for video {video_id}")
            else:
                print(f"   ❌ Error getting comments for video {video_id}: {e}")

        return comments

    def _get_comment_replies(self, parent_id: str, keyword: str = None) -> List[Dict]:
        """
        Get replies to a specific comment.

        Args:
            parent_id: The parent comment ID
            keyword: Optional keyword to filter replies

        Returns:
            List of reply dictionaries
        """
        replies = []

        try:
            request = self.youtube.comments().list(
                part='snippet',
                parentId=parent_id,
                maxResults=10,
                textFormat='plainText'
            )

            response = request.execute()

            for item in response.get('items', []):
                reply_text = item['snippet']['textDisplay']

                # Filter by keyword if provided
                if keyword and keyword.lower() not in reply_text.lower():
                    continue

                replies.append({
                    'id': item['id'],
                    'author': item['snippet']['authorDisplayName'],
                    'text': reply_text,
                    'likes': item['snippet'].get('likeCount', 0),
                    'published_at': item['snippet']['publishedAt']
                })

        except Exception as e:
            print(f"Error getting replies for comment {parent_id}: {e}")

        return replies

    def post_reply(self, comment_id: str, reply_text: str) -> bool:
        """
        Post a reply to a YouTube comment.

        Note: This requires OAuth 2.0 authentication, not just an API key.
        For a basic implementation with API key only, this will return False.

        Args:
            comment_id: The YouTube comment ID
            reply_text: The text of the reply

        Returns:
            bool: True if successful
        """
        try:
            # This requires OAuth 2.0 authentication
            # With just an API key, we can only read data, not post
            print("   ⚠️ YouTube reply requires OAuth 2.0 (not implemented in demo)")
            print(f"   💡 Would reply to {comment_id}: {reply_text[:50]}...")

            # Uncomment when OAuth is implemented:
            # self.youtube.comments().insert(
            #     part='snippet',
            #     body={
            #         'snippet': {
            #             'parentId': comment_id,
            #             'textOriginal': reply_text
            #         }
            #     }
            # ).execute()

            return False  # Set to True when OAuth is implemented

        except Exception as e:
            print(f"Error posting reply to YouTube comment {comment_id}: {e}")
            return False

    def _is_own_post(self, mention: Dict) -> bool:
        """
        Check if the mention is from the bot's own YouTube channel.

        Note: With API key auth, we don't have a clear "own channel" concept.
        Override this if you implement OAuth and want to skip own comments.
        """
        # Could check against config.YOUTUBE_CHANNEL_NAME if set
        if hasattr(self.config, 'YOUTUBE_CHANNEL_NAME'):
            return mention.get('author') == self.config.YOUTUBE_CHANNEL_NAME
        return False
