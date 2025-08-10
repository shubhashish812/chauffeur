"""
Chauffeur Authentication Cloud Function
Handles user registration, login, and authentication operations
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
from models import (
    SignUpRequest, SignInRequest, AuthResponse, ErrorResponse,
    TokenVerificationRequest, TokenVerificationResponse,
    TokenRefreshRequest, TokenRefreshResponse,
    EmailVerificationRequest, EmailVerificationResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.http
def main(request: Request) -> Response:
    """
    Main authentication function handler
    Routes requests to appropriate auth operations
    """
    try:
        # Set CORS headers
        if request.method == 'OPTIONS':
            return _handle_cors()
        
        # Parse request
        request_data = request.get_json() if request.is_json else {}
        path = request.path.strip('/')
        
        logger.info(f"Auth function called: {request.method} {path}")
        
        # Route to appropriate handler
        if path == 'signup' and request.method == 'POST':
            return _handle_signup(request_data)
        elif path == 'signin' and request.method == 'POST':
            return _handle_signin(request_data)
        elif path == 'verify-token' and request.method == 'POST':
            return _handle_verify_token(request_data)
        elif path == 'refresh-token' and request.method == 'POST':
            return _handle_refresh_token(request_data)
        elif path == 'send-verification' and request.method == 'POST':
            return _handle_send_verification(request_data)
        elif path == 'check-verification' and request.method == 'GET':
            return _handle_check_verification(request.args)
        elif path == 'signout' and request.method == 'POST':
            return _handle_signout(request_data)
        elif path == 'health' and request.method == 'GET':
            return _handle_health_check()
        else:
            return _create_error_response("Endpoint not found", 404)
            
    except Exception as e:
        logger.error(f"Unexpected error in auth function: {e}")
        return _create_error_response("Internal server error", 500)

def _handle_signup(request_data: Dict[str, Any]) -> Response:
    """Handle user registration"""
    try:
        # Validate request
        signup_request = SignUpRequest(**request_data)
        
        # Validate password strength
        if not AuthUtils.validate_password(signup_request.password):
            return _create_error_response("Password must be at least 6 characters", 400)
        
        # Create user in Firebase
        user_record = firebase_client.create_user(
            email=signup_request.email,
            password=signup_request.password,
            display_name=signup_request.display_name
        )
        
        # Create custom token
        custom_token = firebase_client.create_custom_token(user_record.uid)
        
        # Send verification email
        try:
            # Exchange custom token for ID token to send verification
            token_data = AuthUtils.exchange_custom_token(custom_token)
            AuthUtils.send_verification_email(token_data['idToken'])
        except Exception as e:
            logger.warning(f"Failed to send verification email: {e}")
        
        # Create response
        response_data = AuthUtils.create_user_response(
            user_record=user_record,
            token=custom_token
        )
        
        return _create_success_response(response_data, 201)
        
    except ValueError as e:
        return _create_error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Error in signup: {e}")
        return _create_error_response("Failed to create user", 500)

def _handle_signin(request_data: Dict[str, Any]) -> Response:
    """Handle user login"""
    try:
        # Validate request
        signin_request = SignInRequest(**request_data)
        
        # Sign in with Firebase REST API
        auth_data = AuthUtils.sign_in_with_password(
            email=signin_request.email,
            password=signin_request.password
        )
        
        # Get user record
        user_record = firebase_client.get_user_by_email(signin_request.email)
        
        # Check email verification
        if not user_record.email_verified:
            return _create_error_response(
                "Email verification required. Please check your email and click the verification link.",
                403
            )
        
        # Create response
        response_data = AuthUtils.create_user_response(
            user_record=user_record,
            token=auth_data['idToken'],
            provider='email'
        )
        
        # Add refresh token if available
        if 'refreshToken' in auth_data:
            response_data['refresh_token'] = auth_data['refreshToken']
            response_data['expires_in'] = auth_data.get('expiresIn')
        
        return _create_success_response(response_data)
        
    except ValueError as e:
        error_msg = str(e)
        if 'EMAIL_NOT_FOUND' in error_msg:
            return _create_error_response("Email not found", 400)
        elif 'INVALID_PASSWORD' in error_msg:
            return _create_error_response("Invalid password", 400)
        else:
            return _create_error_response(error_msg, 400)
    except Exception as e:
        logger.error(f"Error in signin: {e}")
        return _create_error_response("Failed to sign in", 500)

def _handle_verify_token(request_data: Dict[str, Any]) -> Response:
    """Handle token verification"""
    try:
        # Validate request
        token_request = TokenVerificationRequest(**request_data)
        
        # Verify token
        decoded_token = firebase_client.verify_id_token(token_request.token)
        uid = decoded_token['uid']
        
        # Check if user still exists
        try:
            user_record = firebase_client.get_user(uid)
            response_data = {
                "valid": True,
                "uid": uid,
                "email": decoded_token.get('email'),
                "email_verified": decoded_token.get('email_verified', False),
                "user_exists": True
            }
        except Exception:
            response_data = {
                "valid": False,
                "uid": uid,
                "error": "User has been deleted",
                "user_exists": False
            }
        
        return _create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return _create_error_response("Invalid token", 401)

def _handle_refresh_token(request_data: Dict[str, Any]) -> Response:
    """Handle token refresh"""
    try:
        # Validate request
        refresh_request = TokenRefreshRequest(**request_data)
        
        # Refresh token
        token_data = AuthUtils.refresh_id_token(refresh_request.refresh_token)
        
        response_data = {
            "id_token": token_data['id_token'],
            "refresh_token": token_data.get('refresh_token'),
            "expires_in": token_data.get('expires_in'),
            "token_type": token_data.get('token_type', 'Bearer')
        }
        
        return _create_success_response(response_data)
        
    except ValueError as e:
        error_msg = str(e)
        if 'TOKEN_EXPIRED' in error_msg:
            return _create_error_response("Refresh token has expired", 401)
        elif 'INVALID_REFRESH_TOKEN' in error_msg:
            return _create_error_response("Invalid refresh token", 401)
        else:
            return _create_error_response(error_msg, 400)
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return _create_error_response("Failed to refresh token", 500)

def _handle_send_verification(request_data: Dict[str, Any]) -> Response:
    """Handle sending verification email"""
    try:
        # Validate request
        verification_request = EmailVerificationRequest(**request_data)
        
        # Get user record
        user_record = firebase_client.get_user(verification_request.uid)
        
        # Create custom token and exchange for ID token
        custom_token = firebase_client.create_custom_token(verification_request.uid)
        token_data = AuthUtils.exchange_custom_token(custom_token)
        
        # Send verification email
        success = AuthUtils.send_verification_email(token_data['idToken'])
        
        if success:
            response_data = {
                "email_verified": user_record.email_verified,
                "message": "Verification email sent successfully"
            }
            return _create_success_response(response_data)
        else:
            return _create_error_response("Failed to send verification email", 500)
            
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return _create_error_response("Failed to send verification email", 500)

def _handle_check_verification(args: Dict[str, Any]) -> Response:
    """Handle checking verification status"""
    try:
        uid = args.get('uid')
        if not uid:
            return _create_error_response("UID parameter required", 400)
        
        # Get user record
        user_record = firebase_client.get_user(uid)
        
        response_data = {
            "email_verified": user_record.email_verified,
            "message": "Verification status checked successfully"
        }
        
        return _create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error checking verification: {e}")
        return _create_error_response("Failed to check verification status", 500)

def _handle_signout(request_data: Dict[str, Any]) -> Response:
    """Handle user signout"""
    try:
        uid = request_data.get('uid')
        if not uid:
            return _create_error_response("UID parameter required", 400)
        
        # Revoke refresh tokens
        firebase_client.revoke_refresh_tokens(uid)
        
        response_data = {"message": "User signed out successfully"}
        return _create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error in signout: {e}")
        return _create_error_response("Failed to sign out", 500)

def _handle_health_check() -> Response:
    """Handle health check"""
    import time
    response_data = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "chauffeur-auth",
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
