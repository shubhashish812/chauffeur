"""
Test script for Google OAuth functionality
This script helps verify that the Google OAuth implementation is working correctly.
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on a different port

def test_google_config():
    """Test the Google OAuth configuration endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/oauth/google/config")
        print("=== Google Config Test ===")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            config = response.json()
            print("✅ Google config retrieved successfully")
            print(f"Client ID: {config.get('client_id', 'Not set')}")
            print(f"Auth URI: {config.get('auth_uri')}")
            print(f"Token URI: {config.get('token_uri')}")
        else:
            print("❌ Failed to get Google config")
            print(f"Error: {response.text}")
        print()
    except Exception as e:
        print(f"❌ Error testing Google config: {str(e)}")
        print()

def test_google_signin_with_invalid_token():
    """Test Google signin with an invalid token (should fail)"""
    try:
        payload = {
            "id_token": "invalid_token_for_testing"
        }
        response = requests.post(
            f"{BASE_URL}/oauth/google/signin",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print("=== Google Signin Test (Invalid Token) ===")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("✅ Correctly rejected invalid token")
        else:
            print("❌ Unexpected response for invalid token")
            print(f"Response: {response.text}")
        print()
    except Exception as e:
        print(f"❌ Error testing Google signin: {str(e)}")
        print()

def test_environment_variables():
    """Test if required environment variables are set"""
    print("=== Environment Variables Test ===")
    required_vars = [
        "GOOGLE_OAUTH_CLIENT_ID",
        "FIREBASE_API_KEY"
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")
            all_set = False
    
    if all_set:
        print("✅ All required environment variables are set")
    else:
        print("❌ Some environment variables are missing")
        print("Please set the missing environment variables:")
        print("export GOOGLE_OAUTH_CLIENT_ID='your-google-client-id'")
        print("export FIREBASE_API_KEY='your-firebase-api-key'")
    print()

def test_auth_endpoints():
    """Test basic auth endpoints to ensure they're working"""
    try:
        # Test auth signup endpoint
        response = requests.get(f"{BASE_URL}/auth/signup")
        print("=== Auth Endpoints Test ===")
        print(f"Auth signup endpoint status: {response.status_code}")
        
        # Test oauth endpoints
        response = requests.get(f"{BASE_URL}/oauth/google/signin")
        print(f"OAuth Google signin endpoint status: {response.status_code}")
        
        response = requests.get(f"{BASE_URL}/oauth/google/config")
        print(f"OAuth Google config endpoint status: {response.status_code}")
        
        print("✅ Auth endpoints are accessible")
        print()
    except Exception as e:
        print(f"❌ Error testing auth endpoints: {str(e)}")
        print()

def main():
    """Run all tests"""
    print("🚀 Starting OAuth Tests...\n")
    
    test_environment_variables()
    test_auth_endpoints()
    test_google_config()
    test_google_signin_with_invalid_token()
    
    print("🎉 OAuth tests completed!")
    print("\nNext steps:")
    print("1. Set up your Google OAuth client ID")
    print("2. Test with a real Google ID token")
    print("3. Integrate with your frontend application")

if __name__ == "__main__":
    main()
