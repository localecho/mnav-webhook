# 🚀 mNAV Webhook - Quick Reference Card

## 🌐 Live URLs
- **Production**: https://mnav-webhook.vercel.app
- **GitHub**: https://github.com/localecho/mnav-webhook

## 🔧 Essential Commands

### Local Development
```bash
# Navigate to project
cd ~/BlueDuckLLC\ Dropbox/Brigham\ Hall/PYTHON/mnav-webhook

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Test locally
./test_full_flow.sh
```

### Production
```bash
# Deploy to Vercel
vercel --prod

# Test production
./smoke_test_prod.sh

# Force update data
curl -X POST https://mnav-webhook.vercel.app/api/update
```

## 📊 View Different Formulas
- Simple NAV: https://mnav-webhook.vercel.app/?formula=simple
- Enterprise Value: https://mnav-webhook.vercel.app/?formula=ev
- Adjusted NAV: https://mnav-webhook.vercel.app/?formula=adjusted
- Official mNAV: https://mnav-webhook.vercel.app/?formula=official
- BTC per 1000 shares: https://mnav-webhook.vercel.app/?formula=btc
- 30-Day Yield: https://mnav-webhook.vercel.app/?formula=yield

## 🔑 API Endpoints

### Public APIs
```bash
# Get mNAV data
curl https://mnav-webhook.vercel.app/api/mnav | jq '.'

# Check status
curl https://mnav-webhook.vercel.app/api/status | jq '.'

# Health check
curl https://mnav-webhook.vercel.app/api/health
```

### Admin APIs
```bash
# Manual update (replace YOUR_TOKEN)
curl https://mnav-webhook.vercel.app/admin/manual-update?token=YOUR_TOKEN

# Force cache refresh
curl -X POST https://mnav-webhook.vercel.app/api/update
```

## ⚙️ Environment Variables (Vercel)

### Required
```
ADMIN_SECRET_KEY=your-secure-token-here
```

### Recommended (Pick One)
```
SCRAPINGBEE_API_KEY=your-api-key
BROWSERLESS_API_KEY=your-api-key
```

### Optional
```
TWITTER_BEARER_TOKEN=your-token
STOCKTWITS_ACCESS_TOKEN=your-token
```

## 📈 Current Data Sources Priority
1. Playwright scraper (free)
2. ScrapingBee (paid, reliable)
3. Browserless (paid alternative)
4. Twitter/StockTwits (social)
5. TradingView (charts)
6. Manual admin input
7. Cached data (24hr)
8. Fallback (1.79x)

## 🧪 Quick Tests

### Is it working?
```bash
curl -s https://mnav-webhook.vercel.app/api/health | jq '.status'
# Should return: "healthy"
```

### What's the current mNAV?
```bash
curl -s https://mnav-webhook.vercel.app/api/mnav | jq '.data.nav_metrics.official_nav'
# Returns current official mNAV
```

### When was it last updated?
```bash
curl -s https://mnav-webhook.vercel.app/api/status | jq '.cache.age_readable'
# Shows cache age
```

## 🚨 Troubleshooting

### "Fallback value" showing
→ Add API keys in Vercel dashboard

### Admin page 404
→ Admin endpoints work locally, need Vercel route config

### Slow response
→ Cold start normal, warms up after first request

### No daily updates
→ Check Vercel Functions logs for cron execution

## 📱 Mobile View
The site is fully responsive. On mobile, formulas stack vertically for easy selection.

## 🔄 Daily Update Schedule
- **Time**: Midnight UTC (7 PM EST / 4 PM PST)
- **Endpoint**: `/api/cron/daily-update`
- **Automatic**: No action needed

## 💡 Pro Tips
1. Bookmark different formula URLs for quick access
2. Use `/api/mnav` for integration with other tools
3. Set up monitoring on `/api/status` for alerts
4. Admin token works as header or query param

---
*Last updated: January 2025*