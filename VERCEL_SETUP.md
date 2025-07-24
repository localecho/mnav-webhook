# Vercel Environment Configuration Guide

## 🔑 Setting Up API Keys and Environment Variables

### Step 1: Access Vercel Dashboard

1. Go to [https://vercel.com/dashboard](https://vercel.com/dashboard)
2. Click on your `mnav-webhook` project
3. Navigate to "Settings" tab
4. Click on "Environment Variables" in the left sidebar

### Step 2: Required Environment Variables

Add the following environment variables:

#### 1. Admin Authentication
```
Variable Name: ADMIN_SECRET_KEY
Value: [Generate a secure token - e.g., use https://randomkeygen.com/]
Environment: Production, Preview, Development
Description: Token for admin manual update access
```

#### 2. ScrapingBee API (Optional but Recommended)
```
Variable Name: SCRAPINGBEE_API_KEY
Value: [Your ScrapingBee API key]
Environment: Production, Preview
Description: For advanced web scraping with JavaScript rendering
```

To get a ScrapingBee API key:
1. Sign up at [https://www.scrapingbee.com/](https://www.scrapingbee.com/)
2. Free tier includes 1,000 API credits
3. Copy your API key from the dashboard

#### 3. Browserless API (Optional)
```
Variable Name: BROWSERLESS_API_KEY
Value: [Your Browserless API key]
Environment: Production, Preview
Description: Alternative headless browser service
```

To get a Browserless API key:
1. Sign up at [https://www.browserless.io/](https://www.browserless.io/)
2. Free tier available
3. Copy your API key from settings

#### 4. Twitter API (Optional)
```
Variable Name: TWITTER_BEARER_TOKEN
Value: [Your Twitter Bearer Token]
Environment: Production, Preview
Description: For fetching mNAV mentions from Twitter
```

To get a Twitter Bearer Token:
1. Apply for Twitter Developer Account at [https://developer.twitter.com/](https://developer.twitter.com/)
2. Create a new app
3. Generate Bearer Token in "Keys and tokens" section

#### 5. StockTwits API (Optional)
```
Variable Name: STOCKTWITS_ACCESS_TOKEN
Value: [Your StockTwits Access Token]
Environment: Production, Preview
Description: For fetching MSTR discussions
```

### Step 3: Adding Variables in Vercel

1. Click "Add New" button
2. Enter the variable name (e.g., `ADMIN_SECRET_KEY`)
3. Enter the value
4. Select environments (Production, Preview, Development)
5. Click "Save"

### Step 4: Verify Deployment

After adding environment variables:

1. Trigger a new deployment:
   ```bash
   vercel --prod
   ```

2. Check the deployment logs for any errors

3. Test the endpoints:
   ```bash
   # Test admin access (replace YOUR_TOKEN)
   curl https://mnav-webhook.vercel.app/admin/manual-update?token=YOUR_TOKEN
   
   # Check scraping status
   curl https://mnav-webhook.vercel.app/api/status
   ```

### Step 5: Set Up Daily Cron Job

The `vercel.json` already includes a cron configuration:
```json
{
  "crons": [
    {
      "path": "/api/cron/daily-update",
      "schedule": "0 0 * * *"
    }
  ]
}
```

This runs daily at midnight UTC. No additional setup needed!

## 🔒 Security Best Practices

### 1. Generate Strong Admin Token
```bash
# Generate secure token using OpenSSL
openssl rand -base64 32

# Or using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Rotate Keys Regularly
- Change `ADMIN_SECRET_KEY` monthly
- Monitor API key usage for anomalies
- Set up alerts for failed authentication attempts

### 3. Restrict API Key Permissions
- ScrapingBee: Limit to specific domains if possible
- Twitter: Use read-only permissions
- Browserless: Set rate limits

## 🧪 Testing Your Configuration

### Test Script
Create `test_vercel_config.sh`:
```bash
#!/bin/bash

PROD_URL="https://mnav-webhook.vercel.app"
ADMIN_TOKEN="your-admin-token-here"

echo "🔧 Testing Vercel Configuration"
echo "==============================="

# Test public endpoints
echo -e "\n1️⃣ Testing public endpoints:"
echo -n "  Main page: "
curl -s -o /dev/null -w "%{http_code}" $PROD_URL
echo -n "\n  API endpoint: "
curl -s -o /dev/null -w "%{http_code}" $PROD_URL/api/mnav
echo -n "\n  Status: "
curl -s -o /dev/null -w "%{http_code}" $PROD_URL/api/status

# Test admin access
echo -e "\n\n2️⃣ Testing admin access:"
echo -n "  Admin page: "
curl -s -o /dev/null -w "%{http_code}" "$PROD_URL/admin/manual-update?token=$ADMIN_TOKEN"

# Test scraping status
echo -e "\n\n3️⃣ Checking scraping capabilities:"
curl -s $PROD_URL/api/status | jq '.last_successful_scrape'

echo -e "\n\n✅ Configuration test complete!"
```

## 📊 Monitoring Your Deployment

### Vercel Dashboard Monitoring
1. Go to your project dashboard
2. Click on "Functions" tab to see API usage
3. Click on "Analytics" to see traffic patterns
4. Set up alerts in "Settings" → "Notifications"

### API Usage Tracking
Monitor your external API usage:
- ScrapingBee: [https://app.scrapingbee.com/dashboard](https://app.scrapingbee.com/dashboard)
- Browserless: Check your dashboard for usage stats
- Twitter: [https://developer.twitter.com/en/portal/dashboard](https://developer.twitter.com/en/portal/dashboard)

### Custom Monitoring Script
```python
# monitor_apis.py
import requests
import os
from datetime import datetime

def check_api_health():
    """Monitor all configured APIs"""
    
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'apis': {}
    }
    
    # Check ScrapingBee quota
    if os.getenv('SCRAPINGBEE_API_KEY'):
        # Add ScrapingBee quota check
        results['apis']['scrapingbee'] = 'configured'
    
    # Check other APIs...
    
    return results

if __name__ == "__main__":
    print(check_api_health())
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Environment Variables Not Loading
- **Symptom**: Features using API keys don't work
- **Solution**: Redeploy after adding variables
  ```bash
  vercel --prod --force
  ```

#### 2. Admin Access Denied
- **Symptom**: Can't access manual update page
- **Solution**: Verify token matches exactly (no spaces)

#### 3. Scraping Always Falls Back
- **Symptom**: Always shows "Fallback value"
- **Solution**: Check API keys are valid and have credits

#### 4. Cron Job Not Running
- **Symptom**: Data doesn't update at midnight
- **Solution**: Check Vercel Functions logs for cron execution

### Debug Commands
```bash
# Check if environment variables are set
curl https://mnav-webhook.vercel.app/api/debug/env

# Force a scraping attempt
curl -X POST https://mnav-webhook.vercel.app/api/update

# Check last scraping attempt
curl https://mnav-webhook.vercel.app/api/status | jq '.'
```

## 📈 Optimization Tips

### 1. Minimize API Calls
- Use caching effectively (already implemented)
- Only force updates when necessary
- Monitor API credit usage

### 2. Set Up Webhooks
Instead of polling, set up webhooks where possible:
- Twitter Streaming API for real-time mentions
- StockTwits webhooks for MSTR updates

### 3. Implement Fallback Priority
Current priority order:
1. Playwright scraper (free, but requires browser)
2. ScrapingBee (reliable, uses credits)
3. Browserless (alternative to ScrapingBee)
4. Social media APIs (Twitter, StockTwits)
5. Manual updates (admin override)
6. Cached/fallback values

## 🎯 Next Steps

1. **Essential**: Set `ADMIN_SECRET_KEY` immediately
2. **Recommended**: Add at least one scraping API key
3. **Optional**: Add social media API keys for more sources
4. **Monitor**: Check daily that cron updates are working
5. **Maintain**: Review logs weekly for any issues

## 📞 Support Resources

- Vercel Documentation: [https://vercel.com/docs](https://vercel.com/docs)
- ScrapingBee Docs: [https://www.scrapingbee.com/documentation/](https://www.scrapingbee.com/documentation/)
- Browserless Docs: [https://www.browserless.io/docs/](https://www.browserless.io/docs/)
- Twitter API Docs: [https://developer.twitter.com/en/docs](https://developer.twitter.com/en/docs)

## 🎉 Success Checklist

- [ ] Admin token generated and set
- [ ] At least one scraping API configured
- [ ] Manual update tested successfully
- [ ] Daily cron job verified
- [ ] Monitoring set up
- [ ] Documentation bookmarked

Once all items are checked, your mNAV tracker is fully configured and production-ready!