#!/bin/bash
# Full flow test for mNAV webhook

echo "🧪 Testing complete mNAV flow..."
echo "================================"

BASE_URL="${1:-http://localhost:5000}"
ADMIN_TOKEN="${2:-change-me-in-production}"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check initial state
echo -e "\n1️⃣  Checking initial state..."
INITIAL_STATE=$(curl -s $BASE_URL/api/status)
CURRENT_NAV=$(echo $INITIAL_STATE | jq -r '.current_data.official_nav // "null"')
echo -e "   Current mNAV: ${YELLOW}$CURRENT_NAV${NC}"

# 2. Test all display formulas
echo -e "\n2️⃣  Testing all display formulas..."
for formula in simple ev adjusted official btc yield; do
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/?formula=$formula")
    if [ "$STATUS_CODE" = "200" ]; then
        echo -e "   ✓ $formula formula: ${GREEN}OK${NC}"
    else
        echo -e "   ✗ $formula formula: ${RED}FAILED (HTTP $STATUS_CODE)${NC}"
    fi
done

# 3. Test API endpoints
echo -e "\n3️⃣  Testing API endpoints..."
API_ENDPOINTS=("/api/health" "/api/mnav" "/api/status")
for endpoint in "${API_ENDPOINTS[@]}"; do
    RESPONSE=$(curl -s $BASE_URL$endpoint)
    if echo $RESPONSE | jq -e '.success' > /dev/null 2>&1 || echo $RESPONSE | jq -e '.status' > /dev/null 2>&1; then
        echo -e "   ✓ $endpoint: ${GREEN}OK${NC}"
    else
        echo -e "   ✗ $endpoint: ${RED}FAILED${NC}"
    fi
done

# 4. Test admin authentication
echo -e "\n4️⃣  Testing admin authentication..."
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/admin/manual-update?token=wrong-token")
if [ "$AUTH_STATUS" = "401" ]; then
    echo -e "   ✓ Invalid token rejected: ${GREEN}OK${NC}"
else
    echo -e "   ✗ Invalid token accepted: ${RED}SECURITY ISSUE${NC}"
fi

AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/admin/manual-update?token=$ADMIN_TOKEN")
if [ "$AUTH_STATUS" = "200" ]; then
    echo -e "   ✓ Valid token accepted: ${GREEN}OK${NC}"
else
    echo -e "   ✗ Valid token rejected: ${RED}FAILED${NC}"
fi

# 5. Test manual update
echo -e "\n5️⃣  Testing manual update..."
NEW_VALUE="1.88"
UPDATE_RESPONSE=$(curl -s -X POST $BASE_URL/admin/manual-update \
    -d "token=$ADMIN_TOKEN&mnav=$NEW_VALUE&source=Test%20Script&reason=Automated%20test")

if echo "$UPDATE_RESPONSE" | grep -q "Successfully"; then
    echo -e "   ✓ Manual update: ${GREEN}SUCCESS${NC}"
    
    # Verify the update
    sleep 1
    UPDATED_NAV=$(curl -s $BASE_URL/api/mnav | jq -r '.data.nav_metrics.official_nav')
    if [ "$UPDATED_NAV" = "$NEW_VALUE" ]; then
        echo -e "   ✓ Value verified: ${GREEN}$UPDATED_NAV${NC}"
    else
        echo -e "   ✗ Value mismatch: ${RED}Expected $NEW_VALUE, got $UPDATED_NAV${NC}"
    fi
else
    echo -e "   ✗ Manual update: ${RED}FAILED${NC}"
fi

# 6. Test force update
echo -e "\n6️⃣  Testing force update..."
FORCE_UPDATE=$(curl -s -X POST $BASE_URL/api/update)
if echo $FORCE_UPDATE | jq -e '.success' > /dev/null 2>&1; then
    echo -e "   ✓ Force update: ${GREEN}OK${NC}"
else
    echo -e "   ✗ Force update: ${RED}FAILED${NC}"
fi

# 7. Test webhook endpoint
echo -e "\n7️⃣  Testing webhook endpoint..."
WEBHOOK_RESPONSE=$(curl -s -X POST $BASE_URL/webhook/mnav \
    -H "Content-Type: application/json" \
    -d '{"fund_code":"TEST","nav":125.45,"date":"2024-01-01"}')

if echo $WEBHOOK_RESPONSE | jq -e '.success' > /dev/null 2>&1; then
    echo -e "   ✓ Webhook POST: ${GREEN}OK${NC}"
else
    echo -e "   ✗ Webhook POST: ${RED}FAILED${NC}"
fi

# 8. Check cache behavior
echo -e "\n8️⃣  Checking cache status..."
CACHE_INFO=$(curl -s $BASE_URL/api/status | jq '.cache')
CACHE_AGE=$(echo $CACHE_INFO | jq -r '.age_readable // "Unknown"')
HAS_DATA=$(echo $CACHE_INFO | jq -r '.has_data // false')

if [ "$HAS_DATA" = "true" ]; then
    echo -e "   ✓ Cache has data: ${GREEN}YES${NC}"
    echo -e "   ℹ️  Cache age: ${YELLOW}$CACHE_AGE${NC}"
else
    echo -e "   ✗ Cache has data: ${RED}NO${NC}"
fi

# 9. Performance check
echo -e "\n9️⃣  Running performance check..."
START_TIME=$(date +%s.%N)
for i in {1..10}; do
    curl -s $BASE_URL/api/mnav > /dev/null
done
END_TIME=$(date +%s.%N)
AVG_TIME=$(echo "scale=3; ($END_TIME - $START_TIME) / 10" | bc)
echo -e "   ⏱️  Average response time: ${YELLOW}${AVG_TIME}s${NC}"

# Summary
echo -e "\n📊 Test Summary"
echo "================"
echo -e "${GREEN}✅ Test suite completed!${NC}"
echo -e "\nNext steps:"
echo "  1. Deploy to Vercel: vercel --prod"
echo "  2. Set environment variables in Vercel dashboard"
echo "  3. Run this script against production URL"
echo -e "\nProduction test example:"
echo "  ./test_full_flow.sh https://mnav-webhook.vercel.app YOUR_ADMIN_TOKEN"