"""
Chauffeur OAuth Cloud Function
Handles Google OAuth authentication
"""

import functions_framework
import json
import logging
from typing import Dict, Any
from flask import Request, Response
import sys
import os

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from firebase_client import firebase_client
from auth_utils import AuthUtils
from models import OAuthRequest, OAuthConfigResponse, OAuthUserResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.http
def main(request: Request) -> Response:
    """
    Main OAuth function handler
    Routes requests to appropriate OAuth operations
    """
    try:
        # Set CORS headers
        if request.method == 'OPTIONS':
            return _handle_cors()
        
        # Parse request
        request_data = request.get_json() if request.is_json else {}
        path = request.path.strip('/')
        
        logger.info(f"OAuth function called: {request.method} {path}")
        
        # Route to appropriate handler
        if path == 'google' and request.method == 'POST':
            return _handle_google_signin(request_data)
        elif path == 'google/config' and request.method == 'GET':
            return _handle_google_config()
        elif path == 'health' and request.method == 'GET':
            return _handle_health_check()
        else:
            return _create_error_response("Endpoint not found", 404)
            
    except Exception as e:
        logger.error(f"Unexpected error in OAuth function: {e}")
        return _create_error_response("Internal server error", 500)

def _handle_google_signin(request_data: Dict[str, Any]) -> Response:
    """Handle Google OAuth signin"""
    try:
        # Validate request
        oauth_request = OAuthRequest(**request_data)
        
        # Verify Google ID token
        google_user_info = AuthUtils.verify_google_token(oauth_request.id_token)
        
        # Extract user information
        user_info = {
            'email': google_user_info['email'],
            'email_verified': google_user_info.get('email_verified', False),
            'display_name': google_user_info.get('name'),
            'photo_url': google_user_info.get('picture')
        }
        
        # Get or create Firebase user
        user_record = _get_or_create_firebase_user(
            provider='google.com',
            provider_uid=google_user_info['sub'],
            user_info=user_info
        )
        
        # Create custom token for the user
        custom_token = firebase_client.create_custom_token(user_record.uid)
        
        # Create response
        response_data = AuthUtils.create_user_response(
            user_record=user_record,
            token=custom_token,
            provider='google',
            provider_uid=google_user_info['sub']
        )
        
        return _create_success_response(response_data)
        
    except ValueError as e:
        return _create_error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Error in Google signin: {e}")
        return _create_error_response("Failed to authenticate with Google", 500)

def _handle_google_config() -> Response:
    """Handle Google OAuth configuration request"""
    try:
        client_id = AuthUtils.get_google_client_id()
        
        response_data = {
            "client_id": client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "userinfo_uri": "https://www.googleapis.com/oauth2/v3/userinfo"
        }
        
        return _create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting Google config: {e}")
        return _create_error_response("Failed to get OAuth configuration", 500)

def _get_or_create_firebase_user(provider: str, provider_uid: str, user_info: Dict[str, Any]):
    """Get existing user or create new user in Firebase Auth"""
    try:
        # Try to get existing user by email
        user_record = firebase_client.get_user_by_email(user_info['email'])
        
        # User exists, return it (we don't need to link providers for this demo)
        logger.info(f"Found existing user: {user_record.uid}")
        return user_record
        
    except Exception:
        # Create new user
        user_properties = {
            'email': user_info['email'],
            'email_verified': user_info.get('email_verified', False),
            'display_name': user_info.get('display_name'),
            'photo_url': user_info.get('photo_url')
        }
        
        # Remove None values
        user_properties = {k: v for k, v in user_properties.items() if v is not None}
        
        user_record = firebase_client.create_user(**user_properties)
        logger.info(f"Created new user via OAuth: {user_record.uid}")
        return user_record

def _handle_health_check() -> Response:
    """Handle health check"""
    import time
    response_data = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "chauffeur-oauth",
        "version": "1.0.0"
    }
    return _create_success_response(response_data)

def _handle_cors() -> Response:
    """Handle CORS preflight requests"""
    response = Response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

def _create_success_response(data: Dict[str, Any], status_code: int = 200) -> Response:
    """Create success response"""
    import time
    response = Response(
        json.dumps({
            "success": True,
            "data": data,
            "timestamp": time.time()
        }),
        status=status_code,
        content_type='application/json'
    )
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

def _create_error_response(message: str, status_code: int = 400) -> Response:
    """Create error response"""
    import time
    response = Response(
        json.dumps({
            "success": False,
            "error": message,
            "timestamp": time.time()
        }),
        status=status_code,
        content_type='application/json'
    )
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
