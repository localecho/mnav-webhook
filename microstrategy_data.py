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
import time
from functools import wraps
from data_store import DataStore

logger = logging.getLogger(__name__)

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    """Decorator for retrying functions with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = backoff_in_seconds
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1:
                        logger.error(f"Failed after {retries} attempts: {str(e)}")
                        raise
                    else:
                        sleep_time = x * (2 ** i)
                        logger.warning(f"Attempt {i+1} failed, retrying in {sleep_time}s: {str(e)}")
                        time.sleep(sleep_time)
            return None
        return wrapper
    return decorator

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
        self.official_mnav = None
        self.official_mnav_timestamp = None
        self.official_mnav_source = None
        
    def fetch_all_data(self) -> Dict:
        """Fetch all required data and calculate metrics"""
        try:
            # Fetch Bitcoin holdings from saylortracker
            self.btc_holdings = self._fetch_btc_holdings()
            
            # Fetch current Bitcoin price
            self.btc_price = self._fetch_btc_price()
            
            # Fetch MSTR stock data
            self.mstr_data = self._fetch_mstr_data()
            
            # Fetch official mNAV from strategy.com
            self.official_mnav, self.official_mnav_timestamp, self.official_mnav_source = self._fetch_strategy_com_mnav()
            
            # Calculate all metrics
            metrics = self._calculate_all_metrics()
            
            self.last_update = datetime.utcnow()
            
            # Save successful data to storage
            if self.official_mnav and self.official_mnav_source != 'Fallback value (scraping failed)':
                DataStore.save_data(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            # Return mock data as fallback
            return self._get_fallback_data()
    
    @retry_with_backoff(retries=3, backoff_in_seconds=1)
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
    
    async def _try_playwright_scraper(self) -> Optional[Tuple[float, str, str]]:
        """Try to scrape using Playwright (for JavaScript rendering)"""
        try:
            from playwright_scraper import PlaywrightScraper
            import asyncio
            
            scraper = PlaywrightScraper(headless=True)
            result = await scraper.scrape_strategy_com()
            await scraper.close()
            return result
        except Exception as e:
            logger.warning(f"Playwright scraping failed: {e}")
            return None
    
    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def _fetch_strategy_com_mnav(self) -> Tuple[float, str, str]:
        """Fetch official mNAV from strategy.com
        
        Returns:
            Tuple of (mnav_value, timestamp, source_description)
        """
        # First try Playwright for JavaScript rendering
        try:
            import asyncio
            result = asyncio.run(self._try_playwright_scraper())
            if result:
                return result
        except Exception as e:
            logger.warning(f"Playwright not available: {e}")
        
        # Try external scraping services
        try:
            from external_scrapers import external_scraper_manager
            result = external_scraper_manager.scrape_strategy_com()
            if result:
                return result
        except Exception as e:
            logger.warning(f"External scrapers not available: {e}")
        
        # Try alternative data sources (Twitter, StockTwits, etc)
        try:
            from alternative_sources import alternative_data
            result = alternative_data.get_alternative_mnav()
            if result:
                return result
        except Exception as e:
            logger.warning(f"Alternative sources not available: {e}")
        
        # Fallback to regular requests
        try:
            # Headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get('https://www.strategy.com', headers=headers, timeout=10)
            
            logger.info(f"Strategy.com response status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find mNAV value with more specific patterns
                import re
                
                # Look for mNAV patterns in script tags and JSON data
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        # Look for mNAV metric data in JSON
                        # First try specific metric patterns
                        metric_patterns = [
                            r'"name"\s*:\s*"mNAV"[^}]*"value"\s*:\s*(\d+\.?\d*)',
                            r'"mNAV"\s*:\s*{\s*"value"\s*:\s*(\d+\.?\d*)',
                            r'"metric"\s*:\s*"mNAV"[^}]*"current"\s*:\s*(\d+\.?\d*)',
                        ]
                        
                        for pattern in metric_patterns:
                            match = re.search(pattern, script.string, re.IGNORECASE)
                            if match:
                                value = float(match.group(1))
                                logger.info(f"Found mNAV in metric pattern: {value}")
                                if 0.5 <= value <= 5.0:
                                    return (
                                        value,
                                        datetime.utcnow().isoformat() + 'Z',
                                        'Live from strategy.com'
                                    )
                        
                        # Fallback to simple pattern but exclude timestamps
                        # Exclude patterns that look like dates (2025-01-30T20:10:13.741)
                        if 'created_at' not in script.string[:100]:  # Check first 100 chars
                            mnav_match = re.search(r'["\']m[Nn][Aa][Vv]["\']\s*:\s*(\d+\.?\d*)(?![\dT])', script.string)
                            if mnav_match:
                                value = float(mnav_match.group(1))
                                logger.info(f"Found mNAV candidate in script: {value}")
                                if 0.5 <= value <= 5.0:
                                    return (
                                        value,
                                        datetime.utcnow().isoformat() + 'Z',
                                        'Live from strategy.com'
                                    )
                
                # Try to find in page text with context
                text_content = soup.get_text()
                # Look for patterns like "mNAV 1.79" or "mNAV: 1.79x"
                mnav_pattern = re.search(r'mNAV[:\s]+(\d+\.?\d*)x?', text_content, re.IGNORECASE)
                if mnav_pattern:
                    value = float(mnav_pattern.group(1))
                    logger.info(f"Found mNAV candidate in text: {value}")
                    # Validate reasonable range
                    if 0.5 <= value <= 5.0:
                        return (
                            value,
                            datetime.utcnow().isoformat() + 'Z',
                            'Live from strategy.com'
                        )
                    else:
                        logger.warning(f"mNAV value {value} outside expected range (0.5-5.0)")
                
                # Alternative: look for specific class/id
                # mnav_element = soup.find('div', class_='mnav-value')
                # if mnav_element:
                #     return float(mnav_element.text.strip())
            
            logger.warning(f"Failed to scrape strategy.com: Status {response.status_code}")
            
        except Exception as e:
            logger.warning(f"Error fetching strategy.com mNAV: {e}")
        
        # Try to get last successful scrape from storage
        last_successful = DataStore.get_last_successful_mnav()
        if last_successful:
            return (
                last_successful['value'],
                last_successful['timestamp'],
                last_successful['source']
            )
        
        # Return hardcoded fallback as last resort
        return (
            1.79,
            '2025-01-23T00:00:00Z',  # Last known date
            'Fallback value (scraping failed)'
        )
    
    @retry_with_backoff(retries=2, backoff_in_seconds=1)
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
            'official_nav': self.official_mnav,
            'official_nav_timestamp': self.official_mnav_timestamp,
            'official_nav_source': self.official_mnav_source,
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
            'official_nav': 1.79,
            'official_nav_timestamp': '2025-01-23T00:00:00Z',
            'official_nav_source': 'Fallback value',
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