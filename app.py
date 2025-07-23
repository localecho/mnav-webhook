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

@app.route('/')
def home():
    """Root endpoint - Display mNAV in big centered font"""
    # Get mNAV data (you can customize the fund_code here)
    fund_code = request.args.get('fund_code', 'default')
    
    # For now using mock data - replace with actual data fetching
    nav_value = 125.45
    fund_name = f'Sample Fund {fund_code.upper()}'
    change = 1.23
    change_percent = 0.99
    
    # HTML template with big centered mNAV display
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>mNAV Display</title>
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
            @media (max-width: 768px) {
                .nav-value {
                    font-size: 5rem;
                }
                .change {
                    font-size: 1.5rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="fund-name">{{ fund_name }}</div>
            <h1 class="nav-value">{{ "%.2f"|format(nav_value) }}</h1>
            <div class="change {{ 'positive' if change > 0 else 'negative' if change < 0 else 'neutral' }}">
                {{ "+" if change > 0 else "" }}{{ "%.2f"|format(change) }} ({{ "%.2f"|format(change_percent) }}%)
            </div>
            <div class="last-updated">Last updated: {{ timestamp }}</div>
        </div>
        <a href="/api/mnav" class="api-link">API →</a>
        
        <script>
            // Auto-refresh every 30 seconds
            setTimeout(() => location.reload(), 30000);
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(
        html_template,
        fund_name=fund_name,
        nav_value=nav_value,
        change=change,
        change_percent=change_percent,
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
    """Get mNAV data - example implementation"""
    try:
        # Example: Get fund code from query parameter
        fund_code = request.args.get('fund_code', 'default')
        
        # In a real implementation, this would fetch actual mNAV data
        # from a financial API or scrape from a website
        # For demo purposes, returning mock data
        
        mock_data = {
            'fund_code': fund_code,
            'fund_name': f'Sample Fund {fund_code}',
            'nav': 125.45,
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'change': 1.23,
            'change_percent': 0.99,
            'currency': 'USD',
            'last_updated': datetime.utcnow().isoformat(),
            'data_source': 'mock'
        }
        
        # Example of how you might scrape real data:
        # url = f"https://example-fund-site.com/nav/{fund_code}"
        # response = requests.get(url, timeout=10)
        # soup = BeautifulSoup(response.content, 'html.parser')
        # nav_value = soup.find('div', class_='nav-value').text
        # mock_data['nav'] = float(nav_value)
        
        logger.info(f"mNAV data requested for fund: {fund_code}")
        return jsonify({
            'success': True,
            'data': mock_data,
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