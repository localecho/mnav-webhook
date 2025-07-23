#!/usr/bin/env python3
"""
Playwright-based scraper for strategy.com
Uses headless browser to handle JavaScript and avoid bot detection
"""

import asyncio
import logging
from typing import Optional, Tuple
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
from playwright_stealth import stealth_async
import re

logger = logging.getLogger(__name__)

class PlaywrightScraper:
    """Scraper using Playwright for JavaScript-heavy sites"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context = None
        
    async def initialize(self):
        """Initialize browser and context"""
        playwright = await async_playwright().start()
        
        # Use Chromium for better compatibility
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )
        
    async def scrape_strategy_com(self) -> Tuple[float, str, str]:
        """Scrape mNAV from strategy.com using Playwright
        
        Returns:
            Tuple of (mnav_value, timestamp, source_description)
        """
        if not self.browser:
            await self.initialize()
            
        page = None
        try:
            page = await self.context.new_page()
            
            # Apply stealth techniques
            await stealth_async(page)
            
            # Navigate to strategy.com
            logger.info("Navigating to strategy.com with Playwright")
            await page.goto('https://www.strategy.com', wait_until='networkidle')
            
            # Wait for content to load
            await page.wait_for_timeout(3000)  # Wait 3 seconds for dynamic content
            
            # Try multiple strategies to find mNAV
            mnav_value = None
            
            # Strategy 1: Look for mNAV in text content
            page_text = await page.content()
            mnav_match = re.search(r'mNAV[:\s]+(\d+\.?\d*)x?', page_text, re.IGNORECASE)
            if mnav_match:
                value = float(mnav_match.group(1))
                if 0.5 <= value <= 5.0:
                    mnav_value = value
                    logger.info(f"Found mNAV via text search: {value}")
            
            # Strategy 2: Look for specific elements
            if not mnav_value:
                selectors = [
                    '[data-metric="mnav"]',
                    '.mnav-value',
                    '.metric-value:has-text("mNAV")',
                    'div:has-text("mNAV") + div',
                    'span:has-text("mNAV") + span',
                ]
                
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            match = re.search(r'(\d+\.?\d*)', text)
                            if match:
                                value = float(match.group(1))
                                if 0.5 <= value <= 5.0:
                                    mnav_value = value
                                    logger.info(f"Found mNAV via selector {selector}: {value}")
                                    break
                    except:
                        continue
            
            # Strategy 3: Execute JavaScript to find value
            if not mnav_value:
                js_result = await page.evaluate('''
                    () => {
                        // Look for mNAV in various ways
                        const texts = document.body.innerText.match(/mNAV[:\s]+(\d+\.?\d*)/i);
                        if (texts) return texts[1];
                        
                        // Check for data attributes
                        const elem = document.querySelector('[data-mnav]');
                        if (elem) return elem.getAttribute('data-mnav');
                        
                        // Check window variables
                        if (window.mNAV) return window.mNAV;
                        if (window.metrics && window.metrics.mNAV) return window.metrics.mNAV;
                        
                        return null;
                    }
                ''')
                
                if js_result:
                    try:
                        value = float(js_result)
                        if 0.5 <= value <= 5.0:
                            mnav_value = value
                            logger.info(f"Found mNAV via JavaScript: {value}")
                    except:
                        pass
            
            # Take screenshot for debugging
            if not mnav_value:
                screenshot_path = '/tmp/strategy_com_screenshot.png'
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.warning(f"Could not find mNAV, screenshot saved to {screenshot_path}")
            
            if mnav_value:
                return (
                    mnav_value,
                    datetime.utcnow().isoformat() + 'Z',
                    'Live from strategy.com (Playwright)'
                )
            else:
                logger.warning("Playwright scraping did not find valid mNAV")
                return None
                
        except Exception as e:
            logger.error(f"Playwright scraping error: {e}")
            if page:
                try:
                    screenshot_path = '/tmp/strategy_com_error.png'
                    await page.screenshot(path=screenshot_path)
                    logger.info(f"Error screenshot saved to {screenshot_path}")
                except:
                    pass
            return None
        finally:
            if page:
                await page.close()
    
    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()