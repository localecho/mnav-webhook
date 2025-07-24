# mNAV Webhook Testing Guide

## 🧪 Complete Testing Guide for All Features

### 1. Manual Update Feature Testing

#### Test Admin Authentication
```bash
# Test without authentication (should show login form)
curl http://localhost:5000/admin/manual-update

# Test with incorrect token (should fail)
curl http://localhost:5000/admin/manual-update?token=wrong-token

# Test with correct token (use your actual token)
curl http://localhost:5000/admin/manual-update?token=change-me-in-production
```

#### Test Manual Update via Browser
1. Visit: `http://localhost:5000/admin/manual-update`
2. Enter admin token: `change-me-in-production`
3. Submit a test update:
   - mNAV Value: `1.85`
   - Source: `Manual test`
   - Reason: `Testing manual update functionality`
4. Verify update appears on main page

#### Test Manual Update via API
```bash
# POST manual update
curl -X POST http://localhost:5000/admin/manual-update \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "token=change-me-in-production&mnav=1.85&source=API%20Test&reason=Testing%20via%20API"
```

### 2. Scraping Methods Testing

#### Test Playwright Scraper
```python
# Test script: test_playwright.py
import asyncio
from playwright_scraper import PlaywrightScraper

async def test():
    scraper = PlaywrightScraper()
    result = await scraper.scrape_strategy_com()
    print(f"Result: {result}")

asyncio.run(test())
```

#### Test External Scrapers
```python
# Test script: test_external.py
from external_scrapers import external_scraper_manager

# Test ScrapingBee (requires API key)
result = external_scraper_manager.scrape_strategy_com()
print(f"ScrapingBee result: {result}")
```

#### Test Alternative Sources
```python
# Test script: test_alternatives.py
from alternative_sources import AlternativeDataAggregator

aggregator = AlternativeDataAggregator()
data = aggregator.aggregate_mnav_data()
print(f"Alternative sources: {data}")
```

### 3. API Endpoint Testing

#### Main Display
```bash
# Test different formulas
curl http://localhost:5000/?formula=simple
curl http://localhost:5000/?formula=ev
curl http://localhost:5000/?formula=adjusted
curl http://localhost:5000/?formula=official
curl http://localhost:5000/?formula=btc
curl http://localhost:5000/?formula=yield
```

#### API Data Endpoint
```bash
# Get comprehensive mNAV data
curl http://localhost:5000/api/mnav | jq '.'
```

#### Force Update
```bash
# Force cache refresh
curl -X POST http://localhost:5000/api/update
```

#### Scraping Status
```bash
# Check scraping health
curl http://localhost:5000/api/status | jq '.'
```

### 4. Data Persistence Testing

#### Test Data Store
```python
# Test script: test_datastore.py
from data_store import DataStore

# Save test data
test_data = {
    'official_nav': 1.82,
    'official_nav_source': 'Test save',
    'official_nav_timestamp': '2025-01-24T10:00:00Z'
}
DataStore.save_data(test_data)

# Load and verify
loaded = DataStore.load_data()
print(f"Loaded: {loaded}")

# Get last successful
last = DataStore.get_last_successful_mnav()
print(f"Last successful: {last}")
```

### 5. Production Deployment Testing

#### Vercel Deployment
```bash
# Deploy to Vercel
vercel --prod

# Test production endpoints
curl https://mnav-webhook.vercel.app/
curl https://mnav-webhook.vercel.app/api/mnav
curl https://mnav-webhook.vercel.app/api/status
```

#### Environment Variables Testing
```bash
# Set in Vercel dashboard:
ADMIN_SECRET_KEY=your-secure-token-here
SCRAPINGBEE_API_KEY=your-api-key
BROWSERLESS_API_KEY=your-api-key
TWITTER_BEARER_TOKEN=your-token
STOCKTWITS_ACCESS_TOKEN=your-token
```

### 6. Daily Update Testing

#### Test Cron Endpoint
```bash
# Simulate Vercel cron call
curl http://localhost:5000/api/cron/daily-update \
  -H "X-Vercel-Cron: 1"
```

#### Monitor Cache Behavior
```bash
# Check if data updates at midnight UTC
while true; do
  echo "$(date): Checking cache..."
  curl -s http://localhost:5000/api/status | jq '.cache.age_readable'
  sleep 3600  # Check every hour
done
```

### 7. Error Handling Testing

#### Test Invalid Inputs
```bash
# Invalid mNAV value (out of range)
curl -X POST http://localhost:5000/admin/manual-update \
  -d "token=change-me-in-production&mnav=10.0&source=Test&reason=Testing"

# Missing required fields
curl -X POST http://localhost:5000/webhook/mnav \
  -H "Content-Type: application/json" \
  -d '{"fund_code":"TEST"}'
```

#### Test Scraping Failures
```python
# Test with network disconnected
# Should fall back to last known values
```

### 8. Performance Testing

#### Load Testing
```bash
# Install artillery
npm install -g artillery

# Create load test config
cat > load-test.yml << EOF
config:
  target: "http://localhost:5000"
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "Test API"
    flow:
      - get:
          url: "/api/mnav"
      - get:
          url: "/"
EOF

# Run load test
artillery run load-test.yml
```

### 9. Integration Testing

#### Full Flow Test
```bash
# Test complete data flow
./test_full_flow.sh
```

Create `test_full_flow.sh`:
```bash
#!/bin/bash
echo "🧪 Testing complete mNAV flow..."

# 1. Check initial state
echo "1️⃣ Initial state:"
curl -s http://localhost:5000/api/status | jq '.current_data'

# 2. Force update
echo -e "\n2️⃣ Forcing update:"
curl -s -X POST http://localhost:5000/api/update | jq '.'

# 3. Manual update
echo -e "\n3️⃣ Manual update:"
curl -s -X POST http://localhost:5000/admin/manual-update \
  -d "token=change-me-in-production&mnav=1.88&source=Test&reason=Flow test"

# 4. Verify update
echo -e "\n4️⃣ Verify update:"
curl -s http://localhost:5000/api/mnav | jq '.data.nav_metrics.official_nav'

# 5. Check all formulas
echo -e "\n5️⃣ Testing all formulas:"
for formula in simple ev adjusted official btc yield; do
  echo -n "  $formula: "
  curl -s "http://localhost:5000/?formula=$formula" | grep -o '<h1[^>]*>[^<]*</h1>' | sed 's/<[^>]*>//g'
done

echo -e "\n✅ Flow test complete!"
```

### 10. Security Testing

#### Test Authentication
```bash
# Test SQL injection attempts
curl http://localhost:5000/admin/manual-update?token="' OR '1'='1"

# Test XSS attempts
curl -X POST http://localhost:5000/admin/manual-update \
  -d "token=change-me-in-production&mnav=1.8&source=<script>alert('XSS')</script>&reason=Test"
```

## 🚀 Quick Test Commands

### Local Testing Suite
```bash
# Run all tests locally
python -m pytest tests/
```

### Production Smoke Test
```bash
# Quick production health check
./smoke_test_prod.sh
```

Create `smoke_test_prod.sh`:
```bash
#!/bin/bash
PROD_URL="https://mnav-webhook.vercel.app"

echo "🔥 Running production smoke tests..."
echo "=================================="

# Test main page
echo -n "✓ Main page: "
curl -s -o /dev/null -w "%{http_code}" $PROD_URL

echo -n "\n✓ API endpoint: "
curl -s -o /dev/null -w "%{http_code}" $PROD_URL/api/mnav

echo -n "\n✓ Health check: "
curl -s -o /dev/null -w "%{http_code}" $PROD_URL/api/health

echo -n "\n✓ Status check: "
curl -s -o /dev/null -w "%{http_code}" $PROD_URL/api/status

echo -e "\n\n✅ Smoke tests complete!"
```

## 📋 Testing Checklist

- [ ] Manual update authentication works
- [ ] Manual update saves correctly
- [ ] All mNAV formulas display correctly
- [ ] Scraping fallback chain works
- [ ] Cache updates at midnight UTC
- [ ] API endpoints return valid JSON
- [ ] Error handling prevents crashes
- [ ] Security measures block attacks
- [ ] Performance acceptable under load
- [ ] Production deployment successful

## 🐛 Common Issues & Solutions

### Issue: Playwright fails locally
```bash
# Solution: Install browsers
python -m playwright install chromium
```

### Issue: External scrapers return None
```bash
# Solution: Check API keys in .env
echo "SCRAPINGBEE_API_KEY=your-key" >> .env
```

### Issue: Manual update not persisting
```bash
# Solution: Check file permissions
chmod 666 /tmp/mnav_data.json
```

### Issue: Vercel deployment fails
```bash
# Solution: Check requirements.txt
pip freeze > requirements.txt
vercel --prod --force
```