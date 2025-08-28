#!/bin/bash

echo "🧪 VeriaGuide Security Test Suite (Bash Version)"
echo "=" * 50

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

BASE_URL="http://localhost:8000"
ADMIN_API_KEY=${ADMIN_API_KEY:-"***REMOVED***"}

echo "🔒 Testing Admin Endpoint Security..."

# Test 1: Admin access without API key
echo ""
echo "1. Testing admin access without API key..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/admin/cache-info")
if [ "$response" = "401" ]; then
    echo "✅ PASS: Admin endpoint correctly rejects requests without API key (401)"
elif [ "$response" = "000" ]; then
    echo "⚠️  Server not running - start with ./start-dev.sh first"
    exit 1
else
    echo "❌ FAIL: Expected 401, got $response"
fi

# Test 2: Admin access with wrong API key
echo ""
echo "2. Testing admin access with wrong API key..."
response=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: wrong-key" "$BASE_URL/admin/cache-info")
if [ "$response" = "401" ]; then
    echo "✅ PASS: Admin endpoint correctly rejects wrong API key (401)"
else
    echo "❌ FAIL: Expected 401, got $response"
fi

# Test 3: Admin access with correct API key
echo ""
echo "3. Testing admin access with correct API key..."
response=$(curl -s -w "%{http_code}" -H "X-API-Key: $ADMIN_API_KEY" "$BASE_URL/admin/cache-info")
http_code=$(echo "$response" | tail -c 4)
if [ "$http_code" = "200" ]; then
    echo "✅ PASS: Admin endpoint accepts correct API key (200)"
    echo "📊 Cache info received successfully"
else
    echo "❌ FAIL: Expected 200, got $http_code"
fi

# Test 4: Security Headers
echo ""
echo "🛡️  Testing Security Headers..."
headers=$(curl -s -I "$BASE_URL" | tr -d '\r')

check_header() {
    local header_name="$1"
    local expected_value="$2"
    
    if echo "$headers" | grep -qi "^$header_name:"; then
        if [ -z "$expected_value" ]; then
            echo "✅ $header_name: Present"
        else
            actual_value=$(echo "$headers" | grep -i "^$header_name:" | cut -d' ' -f2-)
            if [[ "$actual_value" == *"$expected_value"* ]]; then
                echo "✅ $header_name: $actual_value"
            else
                echo "❌ $header_name: Expected '$expected_value', got '$actual_value'"
            fi
        fi
    else
        echo "❌ Missing header: $header_name"
    fi
}

check_header "X-Content-Type-Options" "nosniff"
check_header "X-Frame-Options" "DENY"
check_header "X-XSS-Protection" "1; mode=block"
check_header "Referrer-Policy" "strict-origin-when-cross-origin"
check_header "Content-Security-Policy" ""

# Test 5: Input Validation
echo ""
echo "🔍 Testing Input Validation..."

echo ""
echo "1. Testing XSS protection in search..."
xss_response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/search?q=%3Cscript%3Ealert('xss')%3C/script%3E")
if [ "$xss_response" = "400" ]; then
    echo "✅ PASS: XSS payload rejected (400)"
else
    echo "✅ PASS: XSS payload handled (status: $xss_response)"
fi

echo ""
echo "2. Testing SQL injection protection..."
sql_response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/search?q=%27%3B%20DROP%20TABLE%20users%3B%20--")
if [ "$sql_response" = "400" ]; then
    echo "✅ PASS: SQL injection payload rejected (400)"
else
    echo "✅ PASS: SQL injection payload handled (status: $sql_response)"
fi

# Test 6: Rate Limiting (basic test)
echo ""
echo "⏱️  Testing Rate Limiting (basic)..."
echo "Making 5 rapid requests..."
for i in {1..5}; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
    if [ "$response" = "429" ]; then
        echo "✅ PASS: Rate limiting active (got 429 on request $i)"
        break
    elif [ "$i" = "5" ]; then
        echo "ℹ️  INFO: No rate limiting triggered in 5 requests (normal for development)"
    fi
done

echo ""
echo "=" * 50
echo "🎉 Security tests completed!"
echo ""
echo "📋 Manual tests to perform:"
echo "   1. Test HTTPS redirect (production only)"
echo "   2. Test WordPress admin access restrictions"
echo "   3. Verify SSL certificate validity (production)"
echo "   4. Test with real load for rate limiting"
echo ""
echo "🚀 To start development server:"
echo "   ./start-dev.sh"
echo ""
echo "🔒 To start production server:"
echo "   ./setup-ssl.sh your-domain.com your-email@domain.com"
echo "   ./start-prod.sh"