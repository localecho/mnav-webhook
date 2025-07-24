#!/bin/bash
# Production smoke test for mNAV webhook

PROD_URL="https://mnav-webhook.vercel.app"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔥 Running production smoke tests...${NC}"
echo "===================================="
echo -e "Target: ${YELLOW}$PROD_URL${NC}"
echo ""

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_code=$2
    local description=$3
    
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_URL$endpoint")
    
    if [ "$STATUS_CODE" = "$expected_code" ]; then
        echo -e "✓ $description: ${GREEN}OK (HTTP $STATUS_CODE)${NC}"
        return 0
    else
        echo -e "✗ $description: ${RED}FAILED (HTTP $STATUS_CODE, expected $expected_code)${NC}"
        return 1
    fi
}

# Function to check JSON response
check_json_endpoint() {
    local endpoint=$1
    local description=$2
    
    RESPONSE=$(curl -s "$PROD_URL$endpoint")
    
    if echo "$RESPONSE" | jq . > /dev/null 2>&1; then
        echo -e "✓ $description: ${GREEN}Valid JSON${NC}"
        
        # Check for success field if present
        if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
            SUCCESS=$(echo "$RESPONSE" | jq -r '.success')
            if [ "$SUCCESS" = "true" ]; then
                echo -e "  └─ Response status: ${GREEN}Success${NC}"
            else
                echo -e "  └─ Response status: ${YELLOW}Success=false${NC}"
            fi
        fi
        return 0
    else
        echo -e "✗ $description: ${RED}Invalid JSON${NC}"
        return 1
    fi
}

# Start tests
TOTAL_TESTS=0
PASSED_TESTS=0

echo -e "${BLUE}📋 Basic Connectivity Tests${NC}"
echo "------------------------"

# Test main page
((TOTAL_TESTS++))
if check_endpoint "/" 200 "Main page"; then ((PASSED_TESTS++)); fi

# Test different formulas
echo -e "\n${BLUE}📊 Formula Display Tests${NC}"
echo "---------------------"
for formula in simple ev adjusted official btc yield; do
    ((TOTAL_TESTS++))
    if check_endpoint "/?formula=$formula" 200 "Formula: $formula"; then ((PASSED_TESTS++)); fi
done

# Test API endpoints
echo -e "\n${BLUE}🔌 API Endpoint Tests${NC}"
echo "------------------"

((TOTAL_TESTS++))
if check_json_endpoint "/api/health" "Health check"; then ((PASSED_TESTS++)); fi

((TOTAL_TESTS++))
if check_json_endpoint "/api/mnav" "mNAV data API"; then ((PASSED_TESTS++)); fi

((TOTAL_TESTS++))
if check_json_endpoint "/api/status" "Status API"; then ((PASSED_TESTS++)); fi

# Test admin endpoint (should require auth)
echo -e "\n${BLUE}🔐 Security Tests${NC}"
echo "---------------"

((TOTAL_TESTS++))
if check_endpoint "/admin/manual-update" 401 "Admin page (no auth)"; then ((PASSED_TESTS++)); fi

((TOTAL_TESTS++))
if check_endpoint "/admin/manual-update?token=invalid" 401 "Admin page (bad auth)"; then ((PASSED_TESTS++)); fi

# Test 404 handling
((TOTAL_TESTS++))
if check_endpoint "/non-existent-endpoint" 404 "404 handling"; then ((PASSED_TESTS++)); fi

# Check current mNAV value
echo -e "\n${BLUE}📈 Current Data Check${NC}"
echo "------------------"
MNAV_DATA=$(curl -s "$PROD_URL/api/mnav")
if echo "$MNAV_DATA" | jq . > /dev/null 2>&1; then
    OFFICIAL_NAV=$(echo "$MNAV_DATA" | jq -r '.data.nav_metrics.official_nav // "N/A"')
    SIMPLE_NAV=$(echo "$MNAV_DATA" | jq -r '.data.nav_metrics.simple_nav // "N/A"')
    BTC_HOLDINGS=$(echo "$MNAV_DATA" | jq -r '.data.bitcoin_metrics.total_btc // "N/A"')
    STOCK_PRICE=$(echo "$MNAV_DATA" | jq -r '.data.stock_metrics.price // "N/A"')
    
    echo -e "Official mNAV: ${YELLOW}${OFFICIAL_NAV}x${NC}"
    echo -e "Simple NAV: ${YELLOW}${SIMPLE_NAV}x${NC}"
    echo -e "BTC Holdings: ${YELLOW}${BTC_HOLDINGS}${NC}"
    echo -e "Stock Price: ${YELLOW}\$${STOCK_PRICE}${NC}"
fi

# Check cache status
echo -e "\n${BLUE}⚡ Cache & Performance${NC}"
echo "-------------------"
CACHE_STATUS=$(curl -s "$PROD_URL/api/status")
if echo "$CACHE_STATUS" | jq . > /dev/null 2>&1; then
    CACHE_AGE=$(echo "$CACHE_STATUS" | jq -r '.cache.age_readable // "Unknown"')
    HAS_DATA=$(echo "$CACHE_STATUS" | jq -r '.cache.has_data // false')
    LAST_SOURCE=$(echo "$CACHE_STATUS" | jq -r '.current_data.official_nav_source // "Unknown"')
    
    echo -e "Cache status: ${HAS_DATA}"
    echo -e "Cache age: ${YELLOW}${CACHE_AGE}${NC}"
    echo -e "Data source: ${YELLOW}${LAST_SOURCE}${NC}"
fi

# Performance test
echo -e "\n${BLUE}⏱️  Response Time Test${NC}"
echo "-------------------"
TOTAL_TIME=0
ITERATIONS=5

for i in $(seq 1 $ITERATIONS); do
    START=$(date +%s.%N)
    curl -s "$PROD_URL/api/mnav" > /dev/null
    END=$(date +%s.%N)
    DIFF=$(echo "$END - $START" | bc)
    TOTAL_TIME=$(echo "$TOTAL_TIME + $DIFF" | bc)
    echo -e "Request $i: ${YELLOW}${DIFF}s${NC}"
done

AVG_TIME=$(echo "scale=3; $TOTAL_TIME / $ITERATIONS" | bc)
echo -e "Average response time: ${YELLOW}${AVG_TIME}s${NC}"

# Final summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "=============="
PERCENTAGE=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)

if [ "$PASSED_TESTS" -eq "$TOTAL_TESTS" ]; then
    echo -e "${GREEN}✅ All tests passed! ($PASSED_TESTS/$TOTAL_TESTS)${NC}"
    EXIT_CODE=0
else
    echo -e "${YELLOW}⚠️  Some tests failed: $PASSED_TESTS/$TOTAL_TESTS passed ($PERCENTAGE%)${NC}"
    EXIT_CODE=1
fi

echo -e "\n${BLUE}📝 Recommendations${NC}"
echo "================"
if [ "$OFFICIAL_NAV" = "N/A" ] || [ "$OFFICIAL_NAV" = "1.79" ]; then
    echo -e "• ${YELLOW}Configure scraping APIs for real-time data${NC}"
fi
if [[ $(echo "$AVG_TIME > 1.0" | bc) -eq 1 ]]; then
    echo -e "• ${YELLOW}Response times are slow, check Vercel function performance${NC}"
fi
echo -e "• ${GREEN}Monitor daily cron job execution in Vercel dashboard${NC}"
echo -e "• ${GREEN}Set up alerts for failed scraping attempts${NC}"

exit $EXIT_CODE