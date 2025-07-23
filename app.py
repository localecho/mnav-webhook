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
    'ttl': 86400  # 24 hours (update once daily)
}

def should_update_at_midnight() -> bool:
    """Check if we should update data (once per day at midnight UTC)"""
    if not _cache['timestamp']:
        return True
    
    last_update = datetime.fromtimestamp(_cache['timestamp'])
    now = datetime.utcnow()
    
    # Update if it's a new day (UTC)
    return last_update.date() < now.date()

def get_cached_mstr_data() -> Dict:
    """Get MicroStrategy data with caching"""
    current_time = time.time()
    
    # Check if cache is valid or if it's past midnight UTC
    if _cache['data'] and not should_update_at_midnight():
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
            .tooltip-container {
                position: relative;
                display: inline-block;
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
            .formula-btn[title] {
                cursor: help;
            }
            .tooltip {
                visibility: hidden;
                background-color: #333;
                color: #fff;
                text-align: left;
                padding: 8px 12px;
                border-radius: 6px;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                transform: translateX(-50%);
                width: 250px;
                font-size: 0.85rem;
                line-height: 1.4;
                opacity: 0;
                transition: opacity 0.3s;
            }
            .tooltip::after {
                content: "";
                position: absolute;
                top: 100%;
                left: 50%;
                margin-left: -5px;
                border-width: 5px;
                border-style: solid;
                border-color: #333 transparent transparent transparent;
            }
            .formula-btn:hover + .tooltip,
            .tooltip:hover {
                visibility: visible;
                opacity: 1;
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
                <div class="tooltip-container">
                    <a href="/?formula=simple" class="formula-btn {{ 'active' if formula == 'simple' else '' }}" 
                       title="Market Cap / BTC Holdings Value">Simple NAV</a>
                    <span class="tooltip">Market Cap ÷ BTC Holdings Value<br><br>The basic premium of MSTR stock price over its Bitcoin holdings</span>
                </div>
                <div class="tooltip-container">
                    <a href="/?formula=ev" class="formula-btn {{ 'active' if formula == 'ev' else '' }}"
                       title="Enterprise Value / BTC Holdings Value">Enterprise Value</a>
                    <span class="tooltip">(Market Cap + Debt - Cash) ÷ BTC Holdings Value<br><br>Accounts for debt and cash positions</span>
                </div>
                <div class="tooltip-container">
                    <a href="/?formula=adjusted" class="formula-btn {{ 'active' if formula == 'adjusted' else '' }}"
                       title="Adjusted for software business">Adjusted NAV</a>
                    <span class="tooltip">(Market Cap + Debt - Cash - Software Value) ÷ BTC Holdings Value<br><br>Excludes estimated software business value</span>
                </div>
                <div class="tooltip-container">
                    <a href="/?formula=official" class="formula-btn {{ 'active' if formula == 'official' else '' }}"
                       title="Official mNAV from strategy.com">Official (Strategy.com)</a>
                    <span class="tooltip">The official mNAV as reported on strategy.com<br><br>May use proprietary calculations</span>
                </div>
                <div class="tooltip-container">
                    <a href="/?formula=btc" class="formula-btn {{ 'active' if formula == 'btc' else '' }}"
                       title="Bitcoin per 1000 shares">BTC/1000 Shares</a>
                    <span class="tooltip">Total BTC Holdings ÷ Shares Outstanding × 1000<br><br>How much Bitcoin you own per 1000 MSTR shares</span>
                </div>
                <div class="tooltip-container">
                    <a href="/?formula=yield" class="formula-btn {{ 'active' if formula == 'yield' else '' }}"
                       title="30-day BTC yield estimate">BTC Yield</a>
                    <span class="tooltip">Estimated 30-day BTC yield based on Saylor's target<br><br>Rough monthly estimate from 6-8% annual target</span>
                </div>
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

@app.route('/admin/manual-update', methods=['GET', 'POST'])
def admin_manual_update():
    """Admin interface for manual mNAV updates"""
    # Simple authentication check
    auth_token = request.headers.get('X-Admin-Token') or request.args.get('token')
    admin_token = os.environ.get('ADMIN_SECRET_KEY', 'change-me-in-production')
    
    if request.method == 'GET':
        # Show manual update form
        if auth_token != admin_token:
            return '''
            <html>
            <head><title>Admin Login</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <h2>Admin Authentication Required</h2>
                <form method="GET">
                    <label>Admin Token: <input type="password" name="token" /></label>
                    <button type="submit">Login</button>
                </form>
            </body>
            </html>
            ''', 401
            
        # Show update form
        return '''
        <html>
        <head>
            <title>Manual mNAV Update</title>
            <style>
                body { font-family: Arial; padding: 20px; background: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
                input, textarea { width: 100%; padding: 8px; margin: 5px 0; }
                button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .current { background: #e3f2fd; padding: 10px; border-radius: 4px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Manual mNAV Update</h2>
                <div class="current">
                    <strong>Current mNAV:</strong> ''' + str(_cache['data'].get('official_nav') if _cache['data'] else 'N/A') + '''<br>
                    <strong>Source:</strong> ''' + str(_cache['data'].get('official_nav_source') if _cache['data'] else 'N/A') + '''
                </div>
                <form method="POST">
                    <input type="hidden" name="token" value="''' + auth_token + '''">
                    <label>mNAV Value: <input type="number" name="mnav" step="0.01" min="0.5" max="5.0" required /></label>
                    <label>Source/Note: <input type="text" name="source" placeholder="e.g., From strategy.com" required /></label>
                    <label>Reason: <textarea name="reason" rows="3" required></textarea></label>
                    <button type="submit">Update mNAV</button>
                </form>
            </div>
        </body>
        </html>
        '''
    
    # Handle POST - update mNAV
    if auth_token != admin_token:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        mnav_value = float(request.form.get('mnav'))
        source = request.form.get('source')
        reason = request.form.get('reason')
        
        # Validate range
        if not (0.5 <= mnav_value <= 5.0):
            return jsonify({'error': 'mNAV must be between 0.5 and 5.0'}), 400
            
        # Update the cache with manual value
        from microstrategy_data import get_microstrategy_data
        from data_store import DataStore
        
        # Get current data
        current_data = get_microstrategy_data()
        
        # Override official mNAV
        current_data['official_nav'] = mnav_value
        current_data['official_nav_source'] = f"Manual: {source}"
        current_data['official_nav_timestamp'] = datetime.utcnow().isoformat() + 'Z'
        current_data['manual_update_reason'] = reason
        
        # Save to storage
        DataStore.save_data(current_data)
        
        # Update cache
        _cache['data'] = current_data
        _cache['timestamp'] = time.time()
        
        logger.info(f"Manual mNAV update: {mnav_value} - {source} - {reason}")
        
        return '''
        <html>
        <head><title>Update Successful</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>✓ mNAV Updated Successfully</h2>
            <p>New value: <strong>''' + str(mnav_value) + '''x</strong></p>
            <p>Source: ''' + source + '''</p>
            <a href="/admin/manual-update?token=''' + auth_token + '''">Update Again</a> | 
            <a href="/">View Site</a>
        </body>
        </html>
        '''
        
    except Exception as e:
        logger.error(f"Manual update error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update', methods=['POST'])
def force_update():
    """Force update of mNAV data (for debugging/manual updates)"""
    try:
        # Clear cache to force update
        _cache['data'] = None
        _cache['timestamp'] = 0
        
        # Get fresh data
        data = get_cached_mstr_data()
        
        return jsonify({
            'success': True,
            'message': 'Data updated successfully',
            'official_nav': data.get('official_nav'),
            'official_nav_source': data.get('official_nav_source'),
            'last_updated': data.get('last_updated'),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error forcing update: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/cron/daily-update', methods=['GET', 'POST'])
def cron_daily_update():
    """Cron job endpoint for daily updates (called by Vercel cron)"""
    try:
        # Verify this is a Vercel cron request (optional security)
        cron_header = request.headers.get('X-Vercel-Cron')
        
        # Clear cache to force update
        _cache['data'] = None
        _cache['timestamp'] = 0
        
        # Get fresh data
        data = get_cached_mstr_data()
        
        logger.info(f"Daily cron update completed. Official mNAV: {data.get('official_nav')}")
        
        return jsonify({
            'success': True,
            'message': 'Daily update completed',
            'official_nav': data.get('official_nav'),
            'official_nav_source': data.get('official_nav_source'),
            'is_cron': bool(cron_header),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Cron update error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/status', methods=['GET'])
def scraping_status():
    """Check scraping status and last update info"""
    try:
        from data_store import DataStore
        
        # Get current cache info
        cache_age = time.time() - _cache['timestamp'] if _cache['timestamp'] else None
        last_data = DataStore.get_last_successful_mnav()
        
        return jsonify({
            'success': True,
            'cache': {
                'has_data': bool(_cache['data']),
                'age_seconds': cache_age,
                'age_readable': f"{cache_age/3600:.1f} hours" if cache_age else "Never updated"
            },
            'last_successful_scrape': last_data,
            'current_data': {
                'official_nav': _cache['data'].get('official_nav') if _cache['data'] else None,
                'official_nav_source': _cache['data'].get('official_nav_source') if _cache['data'] else None
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
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