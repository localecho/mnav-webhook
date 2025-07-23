#!/usr/bin/env python3
"""
External scraping services integration
Supports ScrapingBee, Browserless, and other services
"""

import os
import requests
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class ScrapingBeeClient:
    """ScrapingBee API client for JavaScript rendering"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SCRAPINGBEE_API_KEY')
        self.base_url = 'https://app.scrapingbee.com/api/v1/'
        
    def scrape(self, url: str, render_js: bool = True) -> Optional[str]:
        """Scrape a URL using ScrapingBee"""
        if not self.api_key:
            logger.warning("ScrapingBee API key not configured")
            return None
            
        try:
            params = {
                'api_key': self.api_key,
                'url': url,
                'render_js': 'true' if render_js else 'false',
                'premium_proxy': 'true',
                'country_code': 'us',
                'wait': '3000',  # Wait 3 seconds for JS
                'block_ads': 'true',
                'stealth_proxy': 'true'
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"ScrapingBee error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"ScrapingBee request failed: {e}")
            return None


class BrowserlessClient:
    """Browserless.io API client"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('BROWSERLESS_API_KEY')
        self.base_url = 'https://chrome.browserless.io/content'
        
    def scrape(self, url: str) -> Optional[str]:
        """Scrape a URL using Browserless"""
        if not self.api_key:
            logger.warning("Browserless API key not configured")
            return None
            
        try:
            headers = {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            }
            
            data = {
                'url': url,
                'waitFor': 3000,
                'token': self.api_key,
                'blockAds': True,
                'stealth': True,
                'viewport': {
                    'width': 1920,
                    'height': 1080
                }
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Browserless error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Browserless request failed: {e}")
            return None


class ExternalScraperManager:
    """Manages multiple external scraping services"""
    
    def __init__(self):
        self.scrapingbee = ScrapingBeeClient()
        self.browserless = BrowserlessClient()
        self.services = [
            ('ScrapingBee', self.scrapingbee),
            ('Browserless', self.browserless)
        ]
        
    def scrape_strategy_com(self) -> Tuple[float, str, str]:
        """Try to scrape strategy.com using available external services
        
        Returns:
            Tuple of (mnav_value, timestamp, source_description)
        """
        for service_name, client in self.services:
            if not client.api_key:
                continue
                
            logger.info(f"Trying {service_name} for strategy.com")
            
            try:
                html = client.scrape('https://www.strategy.com')
                if html:
                    mnav_value = self._extract_mnav_from_html(html)
                    if mnav_value:
                        return (
                            mnav_value,
                            datetime.utcnow().isoformat() + 'Z',
                            f'Live from strategy.com ({service_name})'
                        )
            except Exception as e:
                logger.error(f"{service_name} scraping failed: {e}")
                continue
                
        logger.warning("All external scraping services failed")
        return None
        
    def _extract_mnav_from_html(self, html: str) -> Optional[float]:
        """Extract mNAV value from HTML content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try text search
            text_content = soup.get_text()
            mnav_pattern = re.search(r'mNAV[:\s]+(\d+\.?\d*)x?', text_content, re.IGNORECASE)
            if mnav_pattern:
                value = float(mnav_pattern.group(1))
                if 0.5 <= value <= 5.0:
                    logger.info(f"Found mNAV in external scrape: {value}")
                    return value
                else:
                    logger.warning(f"mNAV value {value} outside expected range")
                    
            # Try specific selectors
            selectors = [
                '.mnav-value',
                '[data-metric="mnav"]',
                '.metric:contains("mNAV") + .value',
            ]
            
            for selector in selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        match = re.search(r'(\d+\.?\d*)', element.text)
                        if match:
                            value = float(match.group(1))
                            if 0.5 <= value <= 5.0:
                                return value
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting mNAV from HTML: {e}")
            
        return None


# Singleton instance
external_scraper_manager = ExternalScraperManager()