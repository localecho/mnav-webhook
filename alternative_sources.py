#!/usr/bin/env python3
"""
Alternative data sources for mNAV information
Includes TradingView, social media, and financial APIs
"""

import os
import requests
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import re
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class TradingViewData:
    """Fetch data from TradingView (unofficial)"""
    
    def __init__(self):
        self.base_url = "https://scanner.tradingview.com/america/scan"
        
    def get_mstr_metrics(self) -> Optional[Dict]:
        """Get MSTR metrics from TradingView scanner"""
        try:
            # TradingView scanner API request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Request MSTR data
            data = {
                "symbols": {"tickers": ["NASDAQ:MSTR"], "query": {"types": []}},
                "columns": [
                    "name", "close", "change", "change_abs", "high", "low",
                    "volume", "market_cap_basic", "price_earnings_ttm",
                    "earnings_per_share_basic_ttm", "number_of_employees",
                    "description"
                ]
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('data') and len(result['data']) > 0:
                    mstr_data = result['data'][0]['d']
                    return {
                        'symbol': mstr_data[0],
                        'price': mstr_data[1],
                        'change_percent': mstr_data[2],
                        'change_abs': mstr_data[3],
                        'market_cap': mstr_data[7],
                        'source': 'TradingView'
                    }
            
        except Exception as e:
            logger.error(f"TradingView data fetch failed: {e}")
            
        return None


class SocialMediaMonitor:
    """Monitor social media for mNAV mentions"""
    
    def __init__(self):
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.stocktwits_token = os.getenv('STOCKTWITS_ACCESS_TOKEN')
        
    def search_twitter_mnav(self) -> List[Dict]:
        """Search Twitter for recent mNAV mentions"""
        if not self.twitter_bearer_token:
            logger.warning("Twitter bearer token not configured")
            return []
            
        try:
            headers = {
                'Authorization': f'Bearer {self.twitter_bearer_token}'
            }
            
            # Search for mNAV mentions from key accounts
            params = {
                'query': '(from:saylor OR from:MicroStrategy) mNAV',
                'max_results': 10,
                'tweet.fields': 'created_at,author_id,text'
            }
            
            response = requests.get(
                'https://api.twitter.com/2/tweets/search/recent',
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tweets = []
                for tweet in data.get('data', []):
                    # Look for mNAV values in tweet text
                    text = tweet['text']
                    mnav_match = re.search(r'mNAV[:\s]+(\d+\.?\d*)x?', text, re.IGNORECASE)
                    if mnav_match:
                        tweets.append({
                            'text': text,
                            'mnav_value': float(mnav_match.group(1)),
                            'created_at': tweet['created_at'],
                            'source': 'Twitter'
                        })
                return tweets
                
        except Exception as e:
            logger.error(f"Twitter search failed: {e}")
            
        return []
        
    def get_stocktwits_sentiment(self) -> Optional[Dict]:
        """Get MSTR sentiment from StockTwits"""
        try:
            response = requests.get(
                'https://api.stocktwits.com/api/2/streams/symbol/MSTR.json',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])
                
                # Look for mNAV mentions in recent messages
                for msg in messages[:20]:  # Check last 20 messages
                    body = msg.get('body', '')
                    mnav_match = re.search(r'mNAV[:\s]+(\d+\.?\d*)x?', body, re.IGNORECASE)
                    if mnav_match:
                        return {
                            'mnav_value': float(mnav_match.group(1)),
                            'message': body,
                            'created_at': msg.get('created_at'),
                            'source': 'StockTwits'
                        }
                        
        except Exception as e:
            logger.error(f"StockTwits fetch failed: {e}")
            
        return None


class AlternativeDataAggregator:
    """Aggregates data from multiple alternative sources"""
    
    def __init__(self):
        self.tradingview = TradingViewData()
        self.social_monitor = SocialMediaMonitor()
        
    def get_alternative_mnav(self) -> Optional[Tuple[float, str, str]]:
        """Try to get mNAV from alternative sources
        
        Returns:
            Tuple of (mnav_value, timestamp, source_description)
        """
        # Try social media first (most likely to have mNAV)
        twitter_results = self.social_monitor.search_twitter_mnav()
        if twitter_results:
            latest = twitter_results[0]  # Most recent
            value = latest['mnav_value']
            if 0.5 <= value <= 5.0:
                return (
                    value,
                    latest['created_at'],
                    'Twitter (@saylor or @MicroStrategy)'
                )
                
        # Try StockTwits
        stocktwits_data = self.social_monitor.get_stocktwits_sentiment()
        if stocktwits_data and 'mnav_value' in stocktwits_data:
            value = stocktwits_data['mnav_value']
            if 0.5 <= value <= 5.0:
                return (
                    value,
                    stocktwits_data['created_at'],
                    'StockTwits community'
                )
                
        return None
        
    def get_mstr_supplemental_data(self) -> Dict:
        """Get supplemental MSTR data from alternative sources"""
        data = {}
        
        # Get TradingView data
        tv_data = self.tradingview.get_mstr_metrics()
        if tv_data:
            data['tradingview'] = tv_data
            
        return data


# Singleton instance
alternative_data = AlternativeDataAggregator()