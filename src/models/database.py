import sqlite3
import json
import pickle
from datetime import datetime
import os

class Database:
    def __init__(self, db_name='social_agent.db'):
        # Get the project root directory
        # __file__ is at: <root>/src/models/database.py
        # Go up: models -> src -> root
        current_file = os.path.abspath(__file__)
        models_dir = os.path.dirname(current_file)  # src/models
        src_dir = os.path.dirname(models_dir)        # src
        project_root = os.path.dirname(src_dir)      # project root

        # Build path to database in data directory
        self.db_name = os.path.join(project_root, 'data', db_name)

        # Ensure the data directory exists
        db_dir = os.path.dirname(self.db_name)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        print(f"Database path: {self.db_name}")
        print(f"Database exists: {os.path.exists(self.db_name)}")

        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Table for processed posts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE,
                platform TEXT,
                content TEXT,
                author TEXT,
                intent TEXT,
                sentiment TEXT,
                confidence REAL,
                processed_at TIMESTAMP,
                response_sent TEXT,
                response_type TEXT,
                similarity_score REAL
            )
        ''')
        
        # Table for canned responses with embeddings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS canned_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                response_template TEXT,
                category TEXT,
                intent TEXT,
                embedding BLOB
            )
        ''')
        
        # Performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                total_posts INTEGER,
                canned_used INTEGER,
                ai_generated INTEGER,
                avg_confidence REAL,
                avg_response_time REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # self.add_default_responses()


    # def add_default_responses(self):
    #     defaults = [
    #         {
    #             'keyword': 'pricing',
    #             'response': 'Thanks for your interest! You can find our pricing at [LINK]. Feel free to DM us for custom quotes! 💰',
    #             'category': 'sales',
    #             'intent': 'pricing and costs'
    #         },
    #         {
    #             'keyword': 'support',
    #             'response': "We're here to help! Please DM us your issue or email support@company.com and we'll assist you right away. 🛠️",
    #             'category': 'support',
    #             'intent': 'technical support issue'
    #         },
    #         {
    #             'keyword': 'feature_request',
    #             'response': "Great suggestion! We're always looking to improve. I've passed this to our product team. Thanks for the feedback! 💡",
    #             'category': 'feedback',
    #             'intent': 'feature request'
    #         },
    #         {
    #             'keyword': 'complaint',
    #             'response': "We sincerely apologize for your experience. Please DM us so we can make this right immediately. 🙏",
    #             'category': 'support',
    #             'intent': 'complaint or negative feedback'
    #         },
    #         {
    #             'keyword': 'compliment',
    #             'response': 'Thank you so much! We really appreciate your support! 🙏 ❤️',
    #             'category': 'engagement',
    #             'intent': 'positive feedback'
    #         },
    #         {
    #             'keyword': 'how_to',
    #             'response': 'Great question! Check out our help center at [LINK] or DM us for step-by-step guidance. 📚',
    #             'category': 'support',
    #             'intent': 'general question'
    #         },
    #         {
    #             'keyword': 'availability',
    #             'response': "Yes, we're currently available! You can order directly from [LINK]. Shipping typically takes 3-5 business days. 📦",
    #             'category': 'sales',
    #             'intent': 'general question'
    #         }
    #     ]
        
    #     conn = sqlite3.connect(self.db_name)
    #     cursor = conn.cursor()
        
    #     for item in defaults:
    #         cursor.execute('''
    #             INSERT OR IGNORE INTO canned_responses (keyword, response_template, category, intent)
    #             VALUES (?, ?, ?, ?)
    #         ''', (item['keyword'], item['response'], item['category'], item['intent']))
        
    #     conn.commit()
    #     conn.close()
    
    def get_all_canned_responses(self):
        """Get all canned responses for indexing"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, keyword, response_template, category, intent FROM canned_responses')
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0],
            'keyword': r[1],
            'text': r[2],
            'category': r[3],
            'intent': r[4]
        } for r in results]
    
    def is_processed(self, post_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM processed_posts WHERE post_id = ?', (post_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def mark_processed(self, post_id, platform, content, author, intent, sentiment, 
                      confidence, response, response_type, similarity_score=0.0):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO processed_posts 
            (post_id, platform, content, author, intent, sentiment, confidence, 
             processed_at, response_sent, response_type, similarity_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (post_id, platform, content, author, intent, sentiment, confidence,
              datetime.now(), response, response_type, similarity_score))
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Get performance statistics"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN response_type = 'canned' THEN 1 ELSE 0 END) as canned,
                SUM(CASE WHEN response_type = 'ai' THEN 1 ELSE 0 END) as ai,
                AVG(confidence) as avg_conf,
                AVG(similarity_score) as avg_sim
            FROM processed_posts
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            'total_processed': result[0] or 0,
            'canned_responses': result[1] or 0,
            'ai_responses': result[2] or 0,
            'avg_confidence': result[3] or 0,
            'avg_similarity': result[4] or 0
        }