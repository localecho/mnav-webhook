#!/usr/bin/env python3
"""
mNAV API - Flask application for mutual fund Net Asset Value data
Provides REST API endpoints and webhook capabilities
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
import time
from typing import Dict, Optional

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# In-memory storage for webhook data (use Redis/DB in production)
webhook_data = []

# Simple in-memory cache for MicroStrategy data
_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 300  # 5 minutes
}

def get_cached_mstr_data() -> Dict:
    """Get MicroStrategy data with caching"""
    current_time = time.time()
    
    # Check if cache is valid
    if _cache['data'] and (current_time - _cache['timestamp']) < _cache['ttl']:
        return _cache['data']
    
    # Import here to avoid circular imports
    try:
        from microstrategy_data import get_microstrategy_data
        data = get_microstrategy_data()
        
        # Update cache
        _cache['data'] = data
        _cache['timestamp'] = current_time
        
        return data
    except Exception as e:
        logger.error(f"Error fetching MicroStrategy data: {e}")
        # Return fallback data
        return {
            'simple_nav': 2.5,
            'ev_nav': 2.8,
            'adjusted_nav': 2.9,
            'official_nav': 1.79,
            'official_nav_timestamp': '2025-01-23T00:00:00Z',
            'official_nav_source': 'Fallback value',
            'btc_per_share': 0.00314,
            'btc_per_1000_shares': 3.14,
            'btc_holdings': 607_770,
            'btc_price': 95_000,
            'stock_price': 773.50,
            'btc_yield_30d': 0.6,
            'premium_per_share': 150.0,
            'market_cap': 150_000_000_000,
            'shares_outstanding': 193_500_000,
            'volume': 5_000_000,
            'enterprise_value': 155_800_000_000,
            'total_debt': 6_200_000_000,
            'cash': 400_000_000,
            'btc_value': 57_738_150_000,
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }

@app.route('/')
def home():
    """Root endpoint - Display mNAV in big centered font"""
    # Get formula type from query parameter
    formula = request.args.get('formula', 'simple').lower()
    
    # Get real MicroStrategy data
    data = get_cached_mstr_data()
    
    # Select the appropriate NAV value based on formula
    formula_map = {
        'simple': ('simple_nav', 'Simple NAV Premium'),
        'ev': ('ev_nav', 'Enterprise Value NAV'),
        'adjusted': ('adjusted_nav', 'Adjusted NAV'),
        'official': ('official_nav', 'Official mNAV (Strategy.com)'),
        'btc': ('btc_per_1000_shares', 'BTC per 1000 Shares'),
        'yield': ('btc_yield_30d', '30-Day BTC Yield')
    }
    
    nav_key, formula_name = formula_map.get(formula, ('simple_nav', 'Simple NAV Premium'))
    nav_value = data.get(nav_key, 2.5)
    
    # Format display value based on type
    if formula == 'btc':
        display_value = f"{nav_value:.2f} BTC"
    elif formula == 'yield':
        display_value = f"{nav_value:.1f}%"
    else:
        display_value = f"{nav_value:.2f}x"
    
    # Get timestamp and source info for official mNAV
    official_source = ""
    if formula == 'official':
        official_source = data.get('official_nav_source', '')
        official_timestamp = data.get('official_nav_timestamp', '')
        if official_timestamp:
            try:
                dt = datetime.fromisoformat(official_timestamp.replace('Z', '+00:00'))
                official_source += f" • {dt.strftime('%Y-%m-%d')}"
            except:
                pass
    
    # Additional display data
    btc_holdings = f"{data.get('btc_holdings', 607770):,}"
    stock_price = f"${data.get('stock_price', 773.50):.2f}"
    btc_price = f"${data.get('btc_price', 95000):,}"
    
    # HTML template with big centered mNAV display
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MicroStrategy mNAV</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                margin: 0;
                padding: 0;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: #1a1a1a;
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                overflow: hidden;
            }
            .container {
                text-align: center;
                padding: 2rem;
            }
            .fund-name {
                font-size: 1.5rem;
                color: #888;
                margin-bottom: 1rem;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            .nav-value {
                font-size: 8rem;
                font-weight: 700;
                margin: 0;
                line-height: 1;
                text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
            }
            .change {
                font-size: 2rem;
                margin-top: 1rem;
            }
            .positive {
                color: #4CAF50;
            }
            .negative {
                color: #f44336;
            }
            .neutral {
                color: #888;
            }
            .last-updated {
                font-size: 0.9rem;
                color: #666;
                margin-top: 2rem;
            }
            .api-link {
                position: absolute;
                bottom: 20px;
                right: 20px;
                font-size: 0.8rem;
                color: #666;
                text-decoration: none;
            }
            .api-link:hover {
                color: #999;
            }
            .formula-buttons {
                margin: 2rem 0;
                display: flex;
                gap: 0.5rem;
                justify-content: center;
                flex-wrap: wrap;
            }
            .formula-btn {
                padding: 0.5rem 1rem;
                background: #333;
                border: 1px solid #555;
                color: #fff;
                text-decoration: none;
                border-radius: 4px;
                font-size: 0.9rem;
                transition: all 0.2s;
            }
            .formula-btn:hover {
                background: #444;
                border-color: #777;
            }
            .formula-btn.active {
                background: #4CAF50;
                border-color: #4CAF50;
            }
            .metrics {
                font-size: 1rem;
                color: #aaa;
                margin-top: 1.5rem;
            }
            @media (max-width: 768px) {
                .nav-value {
                    font-size: 5rem;
                }
                .change {
                    font-size: 1.5rem;
                }
                .formula-buttons {
                    flex-direction: column;
                    align-items: center;
                }
                .formula-btn {
                    width: 200px;
                    text-align: center;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="fund-name">MICROSTRATEGY mNAV</div>
            <h1 class="nav-value">{{ display_value }}</h1>
            <div class="change">{{ formula_name }}</div>
            
            <div class="formula-buttons">
                <a href="/?formula=simple" class="formula-btn {{ 'active' if formula == 'simple' else '' }}">Simple NAV</a>
                <a href="/?formula=ev" class="formula-btn {{ 'active' if formula == 'ev' else '' }}">Enterprise Value</a>
                <a href="/?formula=adjusted" class="formula-btn {{ 'active' if formula == 'adjusted' else '' }}">Adjusted NAV</a>
                <a href="/?formula=official" class="formula-btn {{ 'active' if formula == 'official' else '' }}">Official (Strategy.com)</a>
                <a href="/?formula=btc" class="formula-btn {{ 'active' if formula == 'btc' else '' }}">BTC/1000 Shares</a>
                <a href="/?formula=yield" class="formula-btn {{ 'active' if formula == 'yield' else '' }}">BTC Yield</a>
            </div>
            
            <div class="metrics">
                {{ btc_holdings }} BTC • {{ stock_price }}/share • {{ btc_price }}/BTC
            </div>
            
            {% if official_source %}
            <div class="metrics" style="color: #ff9800; margin-top: 0.5rem;">
                {{ official_source }}
            </div>
            {% endif %}
            
            <div class="last-updated">Last updated: {{ timestamp }}</div>
        </div>
        <a href="/api/mnav" class="api-link">API →</a>
        
        <script>
            // Auto-refresh every 5 minutes
            setTimeout(() => location.reload(), 300000);
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(
        html_template,
        display_value=display_value,
        formula_name=formula_name,
        formula=formula,
        btc_holdings=btc_holdings,
        stock_price=stock_price,
        btc_price=btc_price,
        official_source=official_source,
        timestamp=datetime.now().strftime('%H:%M:%S')
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Add any health checks here (DB connection, external services, etc.)
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'mnav-api',
            'version': '1.0.0',
            'uptime': 'running'
        }
        return jsonify(health_status), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@app.route('/api/mnav', methods=['GET'])
def get_mnav():
    """Get MicroStrategy mNAV data"""
    try:
        # Get real MicroStrategy data
        data = get_cached_mstr_data()
        
        # Build comprehensive response
        response_data = {
            'company': 'MicroStrategy Inc.',
            'ticker': 'MSTR',
            'nav_metrics': {
                'simple_nav': data.get('simple_nav', 2.5),
                'enterprise_value_nav': data.get('ev_nav', 2.8),
                'adjusted_nav': data.get('adjusted_nav', 2.9),
                'official_nav': data.get('official_nav', 1.79),
                'official_nav_timestamp': data.get('official_nav_timestamp', ''),
                'official_nav_source': data.get('official_nav_source', ''),
                'premium_per_share': data.get('premium_per_share', 150.0)
            },
            'bitcoin_metrics': {
                'total_btc': data.get('btc_holdings', 607770),
                'btc_per_share': data.get('btc_per_share', 0.00314),
                'btc_per_1000_shares': data.get('btc_per_1000_shares', 3.14),
                'btc_yield_30d': data.get('btc_yield_30d', 0.6),
                'btc_price': data.get('btc_price', 95000)
            },
            'stock_metrics': {
                'price': data.get('stock_price', 773.50),
                'market_cap': data.get('market_cap', 150000000000),
                'shares_outstanding': data.get('shares_outstanding', 193500000),
                'volume': data.get('volume', 5000000)
            },
            'financial_metrics': {
                'enterprise_value': data.get('enterprise_value', 155800000000),
                'total_debt': data.get('total_debt', 6200000000),
                'cash': data.get('cash', 400000000),
                'btc_value': data.get('btc_value', 57738150000)
            },
            'last_updated': data.get('last_updated', datetime.utcnow().isoformat() + 'Z'),
            'data_sources': [
                'Yahoo Finance (MSTR stock data)',
                'CoinGecko/Yahoo (Bitcoin price)',
                'SaylorTracker (BTC holdings)'
            ]
        }
        
        logger.info("MicroStrategy mNAV data requested")
        return jsonify({
            'success': True,
            'data': response_data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching mNAV data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/webhook/mnav', methods=['POST'])
def mnav_webhook():
    """Webhook endpoint to receive mNAV updates"""
    try:
        # Validate webhook request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        # Get webhook data
        data = request.get_json()
        
        # Validate required fields (customize based on your needs)
        required_fields = ['fund_code', 'nav', 'date']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {missing_fields}'
            }), 400
        
        # Process webhook data
        webhook_entry = {
            'id': len(webhook_data) + 1,
            'received_at': datetime.utcnow().isoformat(),
            'data': data,
            'source_ip': request.remote_addr,
            'headers': dict(request.headers)
        }
        
        # Store in memory (use persistent storage in production)
        webhook_data.append(webhook_entry)
        
        # Log the webhook
        logger.info(f"Webhook received for fund: {data.get('fund_code')}")
        
        # In production, you might:
        # - Store in database
        # - Trigger notifications
        # - Update cache
        # - Call other services
        
        return jsonify({
            'success': True,
            'message': 'Webhook received successfully',
            'id': webhook_entry['id'],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/webhook/mnav/history', methods=['GET'])
def webhook_history():
    """Get webhook history (for debugging/monitoring)"""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Calculate pagination
        start = (page - 1) * per_page
        end = start + per_page
        
        # Get paginated data
        total = len(webhook_data)
        items = webhook_data[start:end]
        
        return jsonify({
            'success': True,
            'data': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching webhook history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'timestamp': datetime.utcnow().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'timestamp': datetime.utcnow().isoformat()
    }), 500

if __name__ == '__main__':
    logger.info(f"Starting mNAV API on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)