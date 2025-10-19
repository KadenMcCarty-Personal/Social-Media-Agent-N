import os
import sys

# Add src to path so we can import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.database import Database

# This will print the database path
db = Database()
