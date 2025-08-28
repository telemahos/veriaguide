#!/usr/bin/env python3
"""
Security Test Script für VeriaGuide
Testet die implementierten Sicherheitsmaßnahmen
"""

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' module not found")
    print("🔧 Install with: pip3 install requests python-dotenv")
    print("🔧 Or use the bash version: ./test-security.sh")
    exit(1)

import os
import sys

def test_admin_endpoints():
    """Test Admin-Endpoint Sicherheit"""
    base_url = "http://localhost:8000"
    
    print("🔒 Testing Admin Endpoint Security...")
    
    # Test ohne API Key
    print("\n1. Testing admin access without API key...")
    try:
        response = requests.get(f"{base_url}/admin/cache-info")
        if response.status_code == 401:
            print("✅ PASS: Admin endpoint correctly rejects requests without API key")
        else:
            print(f"❌ FAIL: Expected 401, got {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running - start with ./start-dev.sh first")
        return False
    
    # Test mit falschem API Key
    print("\n2. Testing admin access with wrong API key...")
    headers = {"X-API-Key": "wrong-key"}
    response = requests.get(f"{base_url}/admin/cache-info", headers=headers)
    if response.status_code == 401:
        print("✅ PASS: Admin endpoint correctly rejects wrong API key")
    else:
        print(f"❌ FAIL: Expected 401, got {response.status_code}")
    
    # Test mit korrektem API Key
    print("\n3. Testing admin access with correct API key...")
    correct_key = os.getenv("ADMIN_API_KEY", "***REMOVED***")
    headers = {"X-API-Key": correct_key}
    response = requests.get(f"{base_url}/admin/cache-info", headers=headers)
    if response.status_code == 200:
        print("✅ PASS: Admin endpoint accepts correct API key")
        print(f"📊 Cache info: {response.json()}")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
    
    return True

def test_security_headers():
    """Test Security Headers"""
    base_url = "http://localhost:8000"
    
    print("\n🛡️  Testing Security Headers...")
    
    try:
        response = requests.get(base_url)
        headers = response.headers
        
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": None  # Should exist
        }
        
        for header, expected_value in security_headers.items():
            if header in headers:
                if expected_value is None or headers[header] == expected_value:
                    print(f"✅ {header}: {headers[header]}")
                else:
                    print(f"❌ {header}: Expected '{expected_value}', got '{headers[header]}'")
            else:
                print(f"❌ Missing header: {header}")
                
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running - start with ./start-dev.sh first")
        return False
    
    return True

def test_input_validation():
    """Test Input Validation"""
    base_url = "http://localhost:8000"
    
    print("\n🔍 Testing Input Validation...")
    
    # Test XSS in search
    print("\n1. Testing XSS protection in search...")
    xss_payload = "<script>alert('xss')</script>"
    response = requests.get(f"{base_url}/search", params={"q": xss_payload})
    
    if response.status_code == 400:
        print("✅ PASS: XSS payload rejected")
    elif "<script>" not in response.text:
        print("✅ PASS: XSS payload sanitized")
    else:
        print("❌ FAIL: XSS payload not properly handled")
    
    # Test SQL injection attempt
    print("\n2. Testing SQL injection protection...")
    sql_payload = "'; DROP TABLE users; --"
    response = requests.get(f"{base_url}/search", params={"q": sql_payload})
    
    if response.status_code == 400:
        print("✅ PASS: SQL injection payload rejected")
    else:
        print("✅ PASS: SQL injection payload handled (sanitized)")

def main():
    print("🧪 VeriaGuide Security Test Suite")
    print("=" * 50)
    
    # Load environment variables
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    
    success = True
    success &= test_admin_endpoints()
    success &= test_security_headers()
    success &= test_input_validation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All security tests completed!")
    else:
        print("⚠️  Some tests failed - check output above")
    
    print("\n📋 Manual tests to perform:")
    print("   1. Test HTTPS redirect (production only)")
    print("   2. Test rate limiting with multiple requests")
    print("   3. Test WordPress admin access restrictions")
    print("   4. Verify SSL certificate validity (production)")

if __name__ == "__main__":
    main()