#!/usr/bin/env python3
"""
Basic tests for mNAV webhook application
"""

import unittest
import json
from app import app, get_cached_mstr_data


class TestMNavApp(unittest.TestCase):
    """Test cases for mNAV application"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
    
    def test_home_page_simple_nav(self):
        """Test home page returns HTML with default Simple NAV"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MICROSTRATEGY mNAV', response.data)
        self.assertIn(b'Simple NAV Premium', response.data)
        self.assertIn(b'formula-btn active', response.data)
    
    def test_home_page_ev_nav(self):
        """Test home page with Enterprise Value NAV"""
        response = self.client.get('/?formula=ev')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Enterprise Value NAV', response.data)
    
    def test_api_mnav_endpoint(self):
        """Test mNAV API endpoint returns proper structure"""
        response = self.client.get('/api/mnav')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        # Check main structure
        api_data = data['data']
        self.assertIn('nav_metrics', api_data)
        self.assertIn('bitcoin_metrics', api_data)
        self.assertIn('stock_metrics', api_data)
        self.assertIn('financial_metrics', api_data)
        
        # Check NAV metrics
        nav_metrics = api_data['nav_metrics']
        self.assertIn('simple_nav', nav_metrics)
        self.assertIn('enterprise_value_nav', nav_metrics)
        self.assertIn('adjusted_nav', nav_metrics)
    
    def test_webhook_endpoint(self):
        """Test webhook endpoint accepts POST data"""
        test_data = {
            'fund_code': 'TEST',
            'nav': 100.50,
            'date': '2024-01-01'
        }
        
        response = self.client.post(
            '/webhook/mnav',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('id', data)
    
    def test_webhook_validation(self):
        """Test webhook validates required fields"""
        # Missing required fields
        test_data = {'fund_code': 'TEST'}
        
        response = self.client.post(
            '/webhook/mnav',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_cached_data_structure(self):
        """Test cached MicroStrategy data has expected structure"""
        data = get_cached_mstr_data()
        
        # Check essential fields exist
        self.assertIn('simple_nav', data)
        self.assertIn('ev_nav', data)
        self.assertIn('btc_holdings', data)
        self.assertIn('btc_price', data)
        self.assertIn('stock_price', data)
        
        # Check data types
        self.assertIsInstance(data['simple_nav'], (int, float))
        self.assertIsInstance(data['btc_holdings'], (int, float))
        self.assertGreater(data['btc_holdings'], 0)


if __name__ == '__main__':
    unittest.main()