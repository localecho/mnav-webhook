"""
Vercel serverless function entry point
"""
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects a callable named 'app'
# The Flask app instance is already named 'app', so we can use it directly