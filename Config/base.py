"""
Base Authentication Interface
Abstract base class for all authentication providers
"""

import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from flask import Response, jsonify
from firebase_admin.auth import UserRecord
from shared.firebase_client import firebase_client
from shared.auth_utils import AuthUtils

logger = logging.getLogger(__name__)


class BaseAuthInterface(ABC):
    """
    Abstract base class for authentication interfaces
    Provides common functionality and defines required methods for auth providers
    """
    
    def __init__(self, request_data: Dict[str, Any]):
        """Initialize the auth interface"""
        self.request_data = request_data
    
    # ============================================================================
    # TOKEN MANAGEMENT METHODS (Shared across all interfaces)
    # ============================================================================
    
    def create_custom_token(self, uid: str) -> str:
        """
        Create custom token for user
        Returns Firebase custom token
        """
        try:
            return firebase_client.create_custom_token(uid)
        except Exception as e:
            logger.error(f"Error creating custom token for UID {uid}: {e}")
            raise
    
    def exchange_custom_token_for_id_token(self, custom_token: str) -> Dict[str, Any]:
        """
        Exchange custom token for ID token
        Returns token data with ID token, refresh token, etc.
        """
        try:
            return AuthUtils.exchange_custom_token(custom_token)
        except Exception as e:
            logger.error(f"Error exchanging custom token: {e}")
            raise
    
    def create_authentication_tokens(self, uid: str) -> Dict[str, Any]:
        """
        Create complete authentication token set for user
        Returns custom token and exchanged ID token data
        """
        try:
            # Create custom token
            custom_token = self.create_custom_token(uid)
            
            # Exchange for ID token
            token_data = self.exchange_custom_token_for_id_token(custom_token)
            
            return {
                "custom_token": custom_token,
                "id_token": token_data.get('idToken'),
                "refresh_token": token_data.get('refreshToken'),
                "expires_in": token_data.get('expiresIn'),
                "token_type": "Bearer"
            }
        except Exception as e:
            logger.error(f"Error creating authentication tokens for UID {uid}: {e}")
            raise
    
    def create_user_response_with_tokens(self, user_record: UserRecord, provider: str = None, provider_uid: str = None) -> Dict[str, Any]:
        """
        Create complete user response with authentication tokens
        Returns user data and tokens
        """
        try:
            # Create authentication tokens
            tokens = self.create_authentication_tokens(user_record.uid)
            
            # Create user response
            user_response = AuthUtils.create_user_response(
                user_record=user_record,
                token=tokens['custom_token'],
                provider=provider,
                provider_uid=provider_uid
            )
            
            # Add token information
            user_response.update({
                "tokens": tokens,
                "id_token": tokens['id_token'],
                "refresh_token": tokens['refresh_token'],
                "expires_in": tokens['expires_in']
            })
            
            return user_response
        except Exception as e:
            logger.error(f"Error creating user response with tokens: {e}")
            raise
    
    # ============================================================================
    # STATIC/CLASS METHODS (Shared across all interfaces)
    # ============================================================================
    
    def validate_request(self) -> bool:
        """
        Validate common lambda function inputs
        Returns True if inputs are valid, False otherwise
        """
        if not self.request_data or not isinstance(self.request_data, dict):
            return False        
        return True
    
    @staticmethod
    def create_success_response(data: Dict[str, Any], status_code: int = 200) -> Response:
        """
        Create standardized success response
        Returns Flask Response object
        """
        response_data = {
            "success": True,
            "data": data,
            "timestamp": time.time()
        }
        response = jsonify(response_data)
        response.status_code = status_code
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    @staticmethod
    def create_error_response(message: str, status_code: int = 400) -> Response:
        """
        Create standardized error response
        Returns Flask Response object
        """
        response_data = {
            "success": False,
            "error": message,
            "timestamp": time.time()
        }
        response = jsonify(response_data)
        response.status_code = status_code
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    @staticmethod
    def handle_cors() -> Response:
        """
        Handle CORS preflight requests
        Returns Flask Response object with CORS headers
        """
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response
    
    @staticmethod
    def validate_request_schema(request_data: Dict[str, Any]) -> bool:
        """
        Validate request data against expected schema
        Returns True if schema is valid, False otherwise
        """
        if not isinstance(request_data, dict):
            return False
        
        # Check for required fields
        required_fields = ['type']
        for field in required_fields:
            if field not in request_data:
                return False
        
        return True
    
    # ============================================================================
    # CORE USER APIs (Shared implementations)
    # ============================================================================
    
    def get_user(self, uid: str) -> UserRecord:
        """
        Get user record by UID
        Returns Firebase UserRecord object
        """
        try:
            return firebase_client.get_user(uid)
        except Exception as e:
            logger.error(f"Error getting user by UID {uid}: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> UserRecord:
        """
        Get user record by email address
        Returns Firebase UserRecord object
        """
        try:
            return firebase_client.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token
        Returns decoded token data
        """
        try:
            return firebase_client.verify_id_token(token)
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            raise
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Firebase ID token using refresh token
        Returns new token data
        """
        try:
            return AuthUtils.refresh_id_token(refresh_token)
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise
    
    def send_verification_email(self, uid: str) -> bool:
        """
        Send email verification to user
        Returns True if successful, False otherwise
        """
        try:
            # Create custom token for the user
            custom_token = firebase_client.create_custom_token(uid)
            
            # Exchange custom token for ID token
            token_data = AuthUtils.exchange_custom_token(custom_token)
            
            # Send verification email
            return AuthUtils.send_verification_email(token_data['idToken'])
        except Exception as e:
            logger.error(f"Error sending verification email for UID {uid}: {e}")
            return False
    
    def check_verification_status(self, uid: str) -> bool:
        """
        Check if user's email is verified
        Returns True if verified, False otherwise
        """
        try:
            user_record = self.get_user(uid)
            return user_record.email_verified
        except Exception as e:
            logger.error(f"Error checking verification status for UID {uid}: {e}")
            return False
    
    def signout_user(self, uid: str) -> bool:
        """
        Sign out user and revoke tokens
        Returns True if successful, False otherwise
        """
        try:
            return self.revoke_tokens(uid)
        except Exception as e:
            logger.error(f"Error signing out user {uid}: {e}")
            return False
    
    def revoke_tokens(self, uid: str) -> bool:
        """
        Revoke all refresh tokens for user
        Returns True if successful, False otherwise
        """
        try:
            firebase_client.revoke_refresh_tokens(uid)
            return True
        except Exception as e:
            logger.error(f"Error revoking tokens for UID {uid}: {e}")
            return False
    
    def update_user_profile(self, uid: str, data: Dict[str, Any]) -> UserRecord:
        """
        Update user profile information
        Returns updated UserRecord object
        """
        try:
            # Filter out None values
            update_data = {k: v for k, v in data.items() if v is not None}
            return firebase_client.update_user(uid, **update_data)
        except Exception as e:
            logger.error(f"Error updating user profile for UID {uid}: {e}")
            raise
    
    def delete_user(self, uid: str) -> bool:
        """
        Delete user account
        Returns True if successful, False otherwise
        """
        try:
            firebase_client.delete_user(uid)
            return True
        except Exception as e:
            logger.error(f"Error deleting user {uid}: {e}")
            return False
    
    # ============================================================================
    # ABSTRACT METHODS (Must be implemented by child classes)
    # ============================================================================
    
    @abstractmethod
    def authenticate(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main authentication method - must be implemented by each provider
        Returns authentication response data
        """
        pass
    
    @abstractmethod
    def get_auth_type(self) -> str:
        """
        Get the authentication type identifier
        Returns string identifier (e.g., 'basic', 'google', 'facebook')
        """
        pass
    
    @abstractmethod
    def validate_auth_specific_inputs(self, request_data: Dict[str, Any]) -> bool:
        """
        Validate provider-specific input requirements
        Returns True if inputs are valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_auth_config(self) -> Dict[str, Any]:
        """
        Get provider-specific configuration
        Returns configuration data for the auth provider
        """
        pass
