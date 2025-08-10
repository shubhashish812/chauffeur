"""
Shared authentication utilities for Cloud Functions
Common auth operations, token handling, and validation
"""

import logging
import os
from typing import Any, Dict, Optional

import requests
from firebase_admin import auth

from .firebase_client import firebase_client

logger = logging.getLogger(__name__)


class AuthUtils:
    """Authentication utilities for Cloud Functions"""

    @staticmethod
    def get_firebase_api_key() -> str:
        """Get Firebase API key from environment"""
        api_key = os.getenv("FIREBASE_API_KEY")
        if not api_key:
            raise ValueError("FIREBASE_API_KEY environment variable not set")
        return api_key

    @staticmethod
    def get_google_client_id() -> str:
        """Get Google OAuth client ID from environment"""
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        if not client_id:
            raise ValueError("GOOGLE_OAUTH_CLIENT_ID environment variable not set")
        return client_id

    @staticmethod
    def sign_in_with_password(email: str, password: str) -> Dict[str, Any]:
        """Sign in user with email/password using Firebase REST API"""
        try:
            api_key = AuthUtils.get_firebase_api_key()
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

            payload = {"email": email, "password": password, "returnSecureToken": True}

            response = requests.post(url, json=payload)
            data = response.json()

            if response.status_code != 200:
                error_message = data.get("error", {}).get("message", "Unknown error")
                raise ValueError(error_message)

            return data

        except Exception as e:
            logger.error(f"Error signing in with password: {e}")
            raise

    @staticmethod
    def send_verification_email(id_token: str) -> bool:
        """Send email verification using Firebase REST API"""
        try:
            api_key = AuthUtils.get_firebase_api_key()
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"

            payload = {"requestType": "VERIFY_EMAIL", "idToken": id_token}

            response = requests.post(url, json=payload)

            if response.status_code != 200:
                logger.error(f"Failed to send verification email: {response.text}")
                return False

            logger.info("Verification email sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return False

    @staticmethod
    def exchange_custom_token(custom_token: str) -> Dict[str, Any]:
        """Exchange custom token for ID token"""
        try:
            api_key = AuthUtils.get_firebase_api_key()
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}"

            payload = {"token": custom_token, "returnSecureToken": True}

            response = requests.post(url, json=payload)
            data = response.json()

            if response.status_code != 200:
                error_message = data.get("error", {}).get("message", "Unknown error")
                raise ValueError(error_message)

            return data

        except Exception as e:
            logger.error(f"Error exchanging custom token: {e}")
            raise

    @staticmethod
    def refresh_id_token(refresh_token: str) -> Dict[str, Any]:
        """Refresh ID token using refresh token"""
        try:
            api_key = AuthUtils.get_firebase_api_key()
            url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"

            payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}

            response = requests.post(url, json=payload)
            data = response.json()

            if response.status_code != 200:
                error_message = data.get("error", {}).get("message", "Unknown error")
                raise ValueError(error_message)

            return data

        except Exception as e:
            logger.error(f"Error refreshing ID token: {e}")
            raise

    @staticmethod
    def verify_google_token(id_token: str) -> Dict[str, Any]:
        """Verify Google ID token"""
        try:
            from google.auth.exceptions import GoogleAuthError
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token

            client_id = AuthUtils.get_google_client_id()

            # Verify the token
            idinfo = google_id_token.verify_oauth2_token(
                id_token, google_requests.Request(), client_id
            )

            # Verify the issuer
            if idinfo["iss"] not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                raise ValueError("Wrong issuer.")

            return idinfo

        except GoogleAuthError as e:
            logger.error(f"Google auth error: {e}")
            raise ValueError(f"Invalid Google token: {str(e)}")
        except ValueError as e:
            logger.error(f"Token verification failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error verifying Google token: {e}")
            raise

    @staticmethod
    def create_user_response(
        user_record: auth.UserRecord,
        token: str,
        provider: Optional[str] = None,
        provider_uid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create standardized user response"""
        return {
            "user": {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified,
                "provider": provider,
                "provider_uid": provider_uid,
                "created_at": user_record.user_metadata.creation_timestamp,
                "last_sign_in": user_record.user_metadata.last_sign_in_timestamp,
            },
            "token": token,
        }

    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password strength"""
        if len(password) < 6:
            return False
        return True

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def sanitize_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize user data for storage"""
        # Remove sensitive fields
        sensitive_fields = ["password", "refresh_token", "id_token"]
        sanitized = {k: v for k, v in user_data.items() if k not in sensitive_fields}

        # Ensure required fields
        if "email" not in sanitized:
            raise ValueError("Email is required")

        return sanitized

    @staticmethod
    def get_user_from_token(token: str) -> auth.UserRecord:
        """Get user record from Firebase ID token"""
        try:
            decoded_token = firebase_client.verify_id_token(token)
            uid = decoded_token["uid"]
            return firebase_client.get_user(uid)
        except Exception as e:
            logger.error(f"Error getting user from token: {e}")
            raise

    @staticmethod
    def check_user_permissions(user_uid: str, required_permissions: list[str]) -> bool:
        """Check if user has required permissions"""
        # This is a placeholder for future permission system
        # For now, all authenticated users have basic permissions
        return True

    @staticmethod
    def generate_audit_log(
        action: str, user_uid: str, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate audit log entry"""
        import time

        return {
            "action": action,
            "user_uid": user_uid,
            "timestamp": int(time.time()),
            "details": details,
            "ip_address": details.get("ip_address"),
            "user_agent": details.get("user_agent"),
        }
