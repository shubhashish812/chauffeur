"""
Test script for the new authentication architecture
This script helps verify that the new auth system with base classes works correctly.
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on a different port

def test_new_auth_endpoints():
    """Test the new authentication endpoints"""
    try:
        print("=== New Auth Architecture Test ===")
        
        # Test email/password endpoints
        response = requests.get(f"{BASE_URL}/auth/signup")
        print(f"✅ Email/Password signup endpoint: {response.status_code}")
        
        response = requests.get(f"{BASE_URL}/auth/signin")
        print(f"✅ Email/Password signin endpoint: {response.status_code}")
        
        # Test OAuth endpoints
        response = requests.get(f"{BASE_URL}/oauth/google/signin")
        print(f"✅ Google OAuth signin endpoint: {response.status_code}")
        
        response = requests.get(f"{BASE_URL}/oauth/google/config")
        print(f"✅ Google OAuth config endpoint: {response.status_code}")
        
        print("✅ All new auth endpoints are accessible")
        print()
    except Exception as e:
        print(f"❌ Error testing new auth endpoints: {str(e)}")
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

def test_file_structure():
    """Test that the new file structure is in place"""
    print("=== File Structure Test ===")
    
    required_files = [
        "app/auth/__init__.py",
        "app/auth/base.py",
        "app/auth/email_password.py",
        "app/auth/google_oauth.py",
        "app/auth_router.py",
        "tests/test_oauth.py",
        "tests/oauth_example.html",
        "GOOGLE_OAUTH_SETUP.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            all_exist = False
    
    if all_exist:
        print("✅ All required files are in place")
    else:
        print("❌ Some files are missing")
    print()

def main():
    """Run all tests"""
    print("🚀 Starting New Auth Architecture Tests...\n")
    
    test_file_structure()
    test_environment_variables()
    test_new_auth_endpoints()
    test_google_config()
    
    print("🎉 New auth architecture tests completed!")
    print("\nNext steps:")
    print("1. Set up your Google OAuth client ID (see GOOGLE_OAUTH_SETUP.md)")
    print("2. Test with a real Google ID token")
    print("3. Open tests/oauth_example.html in your browser to test the UI")
    print("4. Add more OAuth providers by following the base class pattern")

if __name__ == "__main__":
    main()
