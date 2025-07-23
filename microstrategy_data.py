#!/usr/bin/env python3
"""
MicroStrategy data fetcher and mNAV calculator
Fetches real-time data and calculates various NAV metrics
"""

import requests
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MicroStrategyData:
    """Fetches and calculates MicroStrategy mNAV metrics"""
    
    # Known values (update these periodically or fetch dynamically)
    MSTR_TICKER = "MSTR"
    SAYLORTRACKER_URL = "https://saylortracker.com"
    
    # Debt and financial data (as of late 2024, update as needed)
    TOTAL_DEBT = 6_200_000_000  # $6.2B in convertible notes
    CASH_POSITION = 400_000_000  # Approximate cash
    SOFTWARE_BUSINESS_VALUE = 500_000_000  # Estimated value of software business
    
    def __init__(self):
        self.btc_holdings = None
        self.btc_price = None
        self.mstr_data = None
        self.last_update = None
        
    def fetch_all_data(self) -> Dict:
        """Fetch all required data and calculate metrics"""
        try:
            # Fetch Bitcoin holdings from saylortracker
            self.btc_holdings = self._fetch_btc_holdings()
            
            # Fetch current Bitcoin price
            self.btc_price = self._fetch_btc_price()
            
            # Fetch MSTR stock data
            self.mstr_data = self._fetch_mstr_data()
            
            # Calculate all metrics
            metrics = self._calculate_all_metrics()
            
            self.last_update = datetime.utcnow()
            return metrics
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            # Return mock data as fallback
            return self._get_fallback_data()
    
    def _fetch_btc_holdings(self) -> float:
        """Scrape Bitcoin holdings from saylortracker.com"""
        try:
            response = requests.get(self.SAYLORTRACKER_URL, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for Bitcoin holdings in various possible locations
            # This is a simplified example - actual scraping would need to be more robust
            btc_text = soup.find(text=lambda t: t and 'BTC' in t and ',' in t)
            if btc_text:
                # Extract number from text like "607,770 BTC"
                btc_str = btc_text.strip().replace(',', '').replace('BTC', '').strip()
                return float(btc_str)
                
            # Fallback to known recent value
            return 607_770
            
        except Exception as e:
            logger.warning(f"Failed to scrape BTC holdings: {e}")
            # Return last known value
            return 607_770
    
    def _fetch_btc_price(self) -> float:
        """Fetch current Bitcoin price from multiple sources"""
        try:
            # Try CoinGecko API (free tier)
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data['bitcoin']['usd']
        except:
            pass
        
        try:
            # Fallback to Yahoo Finance
            btc = yf.Ticker("BTC-USD")
            return btc.info.get('regularMarketPrice', 95000)
        except:
            pass
            
        # Fallback price
        return 95_000
    
    def _fetch_mstr_data(self) -> Dict:
        """Fetch MicroStrategy stock data from Yahoo Finance"""
        try:
            mstr = yf.Ticker(self.MSTR_TICKER)
            info = mstr.info
            
            # Get real-time quote
            quote = mstr.fast_info
            
            return {
                'price': quote['lastPrice'] if hasattr(quote, 'lastPrice') else info.get('currentPrice', 773.50),
                'market_cap': quote['marketCap'] if hasattr(quote, 'marketCap') else info.get('marketCap', 150_000_000_000),
                'shares_outstanding': info.get('sharesOutstanding', 193_500_000),
                'volume': quote['lastVolume'] if hasattr(quote, 'lastVolume') else info.get('volume', 5_000_000),
            }
        except Exception as e:
            logger.warning(f"Failed to fetch MSTR data: {e}")
            # Return fallback data
            return {
                'price': 773.50,
                'market_cap': 150_000_000_000,
                'shares_outstanding': 193_500_000,
                'volume': 5_000_000,
            }
    
    def _calculate_all_metrics(self) -> Dict:
        """Calculate all mNAV metrics"""
        btc_value = self.btc_holdings * self.btc_price
        market_cap = self.mstr_data['market_cap']
        shares = self.mstr_data['shares_outstanding']
        
        # Calculate different NAV formulas
        simple_nav = market_cap / btc_value
        
        # Enterprise Value NAV
        enterprise_value = market_cap + self.TOTAL_DEBT - self.CASH_POSITION
        ev_nav = enterprise_value / btc_value
        
        # Adjusted NAV (excluding software business)
        adjusted_market_cap = market_cap + self.TOTAL_DEBT - self.CASH_POSITION - self.SOFTWARE_BUSINESS_VALUE
        adjusted_nav = adjusted_market_cap / btc_value
        
        # Bitcoin per share
        btc_per_share = self.btc_holdings / shares
        btc_per_1000_shares = btc_per_share * 1000
        
        # NAV per share
        nav_per_share = (btc_value - self.TOTAL_DEBT + self.CASH_POSITION) / shares
        premium_per_share = ((self.mstr_data['price'] - nav_per_share) / nav_per_share) * 100
        
        # Calculate 30-day BTC yield (would need historical data for accurate calc)
        # For now, using Saylor's target of 6-8% annually
        btc_yield_annual = 7.0  # percent
        btc_yield_30d = btc_yield_annual / 12  # rough monthly estimate
        
        return {
            'simple_nav': round(simple_nav, 2),
            'ev_nav': round(ev_nav, 2),
            'adjusted_nav': round(adjusted_nav, 2),
            'btc_per_share': btc_per_share,
            'btc_per_1000_shares': round(btc_per_1000_shares, 2),
            'nav_per_share': round(nav_per_share, 2),
            'premium_per_share': round(premium_per_share, 1),
            'btc_yield_30d': round(btc_yield_30d, 1),
            'btc_holdings': self.btc_holdings,
            'btc_value': int(btc_value),
            'btc_price': int(self.btc_price),
            'market_cap': int(market_cap),
            'enterprise_value': int(enterprise_value),
            'total_debt': self.TOTAL_DEBT,
            'cash': self.CASH_POSITION,
            'stock_price': round(self.mstr_data['price'], 2),
            'shares_outstanding': shares,
            'volume': self.mstr_data['volume'],
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _get_fallback_data(self) -> Dict:
        """Return fallback data when APIs fail"""
        return {
            'simple_nav': 2.5,
            'ev_nav': 2.8,
            'adjusted_nav': 2.9,
            'btc_per_share': 0.00314,
            'btc_per_1000_shares': 3.14,
            'nav_per_share': 309.40,
            'premium_per_share': 150.0,
            'btc_yield_30d': 0.6,
            'btc_holdings': 607_770,
            'btc_value': 57_738_150_000,
            'btc_price': 95_000,
            'market_cap': 150_000_000_000,
            'enterprise_value': 155_800_000_000,
            'total_debt': 6_200_000_000,
            'cash': 400_000_000,
            'stock_price': 773.50,
            'shares_outstanding': 193_500_000,
            'volume': 5_000_000,
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }


def get_microstrategy_data() -> Dict:
    """Main function to get MicroStrategy data"""
    fetcher = MicroStrategyData()
    return fetcher.fetch_all_data()