#!/usr/bin/env python3
"""
Persistent data storage for mNAV data
Uses JSON file for simplicity, can be upgraded to database
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Use /tmp for Vercel deployment (ephemeral but works for the function lifetime)
DATA_FILE = os.environ.get('DATA_FILE_PATH', '/tmp/mnav_data.json')

class DataStore:
    """Simple persistent storage for mNAV data"""
    
    @staticmethod
    def save_data(data: Dict) -> bool:
        """Save data to JSON file"""
        try:
            # Add timestamp if not present
            if 'stored_at' not in data:
                data['stored_at'] = datetime.utcnow().isoformat() + 'Z'
            
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Data saved to {DATA_FILE}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return False
    
    @staticmethod
    def load_data() -> Optional[Dict]:
        """Load data from JSON file"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                # Check if data is from today (UTC)
                if 'stored_at' in data:
                    stored_time = datetime.fromisoformat(data['stored_at'].replace('Z', '+00:00'))
                    if stored_time.date() == datetime.utcnow().date():
                        logger.info(f"Loaded today's data from {DATA_FILE}")
                        return data
                    else:
                        logger.info("Stored data is from a previous day")
                
            return None
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return None
    
    @staticmethod
    def get_last_successful_mnav() -> Optional[Dict]:
        """Get the last successfully scraped official mNAV"""
        try:
            data = DataStore.load_data()
            if data and 'official_nav' in data:
                return {
                    'value': data.get('official_nav'),
                    'timestamp': data.get('official_nav_timestamp'),
                    'source': 'Last successful scrape'
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get last mNAV: {e}")
            return None