"""
Google OAuth Authentication Interface
Handles Google OAuth authentication operations
"""

import logging
import time
from typing import Any, Dict

import requests

from Config.models import GoogleAuthData
from shared.auth_utils import AuthUtils
from shared.firebase_client import firebase_client

from .base import BaseAuthInterface

logger = logging.getLogger(__name__)


class GoogleAuthInterface(BaseAuthInterface):
    """
    Google OAuth authentication interface
    Handles Google OAuth authentication and user management
    """

    def __init__(self, request_data: Dict[str, Any]):
        """Initialize Google OAuth interface"""
        super().__init__(request_data)
        self.request_data = request_data

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def signin(self) -> Dict[str, Any]:
        """
        Authenticate user with Google OAuth
        Returns user data and authentication tokens
        """
        try:
            # Validate data using Pydantic model
            google_data = GoogleAuthData(**self.request_data["data"])

            # Verify Google token and get user info
            google_user_info = self.get_google_user_info(google_data.id_token)

            # Get or create Firebase user
            user_record = self.get_or_create_google_user(google_user_info)

            # Create complete user response with tokens
            response_data = self.create_user_response_with_tokens(
                user_record=user_record,
                provider="google",
                provider_uid=google_user_info["sub"],
            )

            # Add Google-specific data
            response_data["google_user_info"] = {
                "name": google_user_info.get("name"),
                "picture": google_user_info.get("picture"),
                "locale": google_user_info.get("locale"),
                "hd": google_user_info.get("hd"),
            }

            return response_data

        except Exception as e:
            logger.error(f"Error in Google OAuth signin: {e}")
            raise

    # ============================================================================
    # GOOGLE OAUTH SPECIFIC METHODS
    # ============================================================================

    def verify_google_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Google ID token
        Returns decoded Google user information
        """
        try:
            return AuthUtils.verify_google_token(id_token)
        except Exception as e:
            logger.error(f"Error verifying Google token: {e}")
            raise

    def get_google_user_info(self, id_token: str) -> Dict[str, Any]:
        """
        Extract user information from Google ID token
        Returns user profile data from Google
        """
        try:
            # Verify the token first
            google_user_info = self.verify_google_token(id_token)

            # Extract relevant user information
            user_info = {
                "email": google_user_info.get("email"),
                "email_verified": google_user_info.get("email_verified", False),
                "name": google_user_info.get("name"),
                "given_name": google_user_info.get("given_name"),
                "family_name": google_user_info.get("family_name"),
                "picture": google_user_info.get("picture"),
                "sub": google_user_info.get("sub"),  # Google user ID
                "locale": google_user_info.get("locale"),
                "hd": google_user_info.get("hd"),  # Hosted domain (for G Suite)
            }

            return user_info

        except Exception as e:
            logger.error(f"Error getting Google user info: {e}")
            raise

    def get_or_create_google_user(self, google_user_info: Dict[str, Any]):
        """
        Get existing user or create new user from Google data
        Returns Firebase UserRecord
        """
        try:
            email = google_user_info["email"]

            # Try to get existing user by email
            try:
                user_record = self.get_user_by_email(email)
                logger.info(f"Found existing user: {user_record.uid}")
                return user_record
            except Exception:
                # User doesn't exist, create new one
                pass

            # Create new user
            user_properties = {
                "email": email,
                "email_verified": google_user_info.get("email_verified", False),
                "display_name": google_user_info.get("name"),
                "photo_url": google_user_info.get("picture"),
            }

            # Remove None values
            user_properties = {
                k: v for k, v in user_properties.items() if v is not None
            }

            user_record = firebase_client.create_user(**user_properties)
            logger.info(f"Created new user via Google OAuth: {user_record.uid}")

            return user_record

        except Exception as e:
            logger.error(f"Error getting or creating Google user: {e}")
            raise

    def link_google_account(self, uid: str, google_user_info: Dict[str, Any]) -> bool:
        """
        Link Google account to existing Firebase user
        Returns True if linking successful
        """
        try:
            # This is a placeholder for account linking
            # In a real implementation, you would:
            # 1. Store Google user ID in user's custom claims
            # 2. Update user profile with Google information
            # 3. Handle potential conflicts

            # For now, just update the user profile
            update_data = {}
            if google_user_info.get("name"):
                update_data["display_name"] = google_user_info["name"]
            if google_user_info.get("picture"):
                update_data["photo_url"] = google_user_info["picture"]

            if update_data:
                self.update_user_profile(uid, update_data)

            logger.info(f"Google account linked for UID {uid}")
            return True

        except Exception as e:
            logger.error(f"Error linking Google account for UID {uid}: {e}")
            return False

    def unlink_google_account(self, uid: str) -> bool:
        """
        Unlink Google account from Firebase user
        Returns True if unlinking successful
        """
        try:
            # This is a placeholder for account unlinking
            # In a real implementation, you would:
            # 1. Remove Google user ID from custom claims
            # 2. Clear Google-specific profile data
            # 3. Ensure user has alternative login method

            logger.info(f"Google account unlinked for UID {uid}")
            return True

        except Exception as e:
            logger.error(f"Error unlinking Google account for UID {uid}: {e}")
            return False

    def get_google_oauth_config(self) -> Dict[str, Any]:
        """
        Get Google OAuth configuration
        Returns client ID, endpoints, etc.
        """
        try:
            client_id = AuthUtils.get_google_client_id()

            return {
                "client_id": client_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "userinfo_uri": "https://www.googleapis.com/oauth2/v3/userinfo",
                "revoke_uri": "https://oauth2.googleapis.com/revoke",
                "scopes": ["openid", "email", "profile"],
            }

        except Exception as e:
            logger.error(f"Error getting Google OAuth config: {e}")
            raise

    def refresh_google_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Google access token
        Returns new token data
        """
        try:
            client_id = AuthUtils.get_google_client_id()

            url = "https://oauth2.googleapis.com/token"
            payload = {
                "client_id": client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }

            response = requests.post(url, data=payload)

            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"Failed to refresh Google token: {response.text}")

        except Exception as e:
            logger.error(f"Error refreshing Google token: {e}")
            raise

    def revoke_google_access(self, uid: str) -> bool:
        """
        Revoke Google access for user
        Returns True if revocation successful
        """
        try:
            # This is a placeholder for Google access revocation
            # In a real implementation, you would:
            # 1. Get user's Google refresh token
            # 2. Call Google's revoke endpoint
            # 3. Clear stored tokens

            logger.info(f"Google access revoked for UID {uid}")
            return True

        except Exception as e:
            logger.error(f"Error revoking Google access for UID {uid}: {e}")
            return False

    # ============================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS
    # ============================================================================

    def authenticate(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy authenticate method - now routes to specific action methods
        """
        action = request_data.get("action", "signin")
        if hasattr(self, action):
            return getattr(self, action)()
        else:
            raise ValueError(f"Unsupported action: {action}")

    def get_auth_type(self) -> str:
        """Get the authentication type identifier"""
        return "google"

    def validate_auth_specific_inputs(self, request_data: Dict[str, Any]) -> bool:
        """
        Validate Google OAuth specific input requirements
        Pydantic models handle validation automatically
        """
        return True

    def get_auth_config(self) -> Dict[str, Any]:
        """
        Get Google OAuth configuration
        Returns client ID, auth endpoints, etc.
        """
        return {
            "auth_type": "google",
            "client_id": AuthUtils.get_google_client_id(),
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "userinfo_uri": "https://www.googleapis.com/oauth2/v3/userinfo",
            "revoke_uri": "https://oauth2.googleapis.com/revoke",
            "scopes": ["openid", "email", "profile"],
            "supported_actions": ["signin"],
        }

    # ============================================================================
    # GOOGLE API METHODS
    # ============================================================================

    def get_google_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Get user profile from Google People API
        Returns detailed user profile information
        """
        try:
            url = "https://people.googleapis.com/v1/people/me"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }
            params = {
                "personFields": "names,emailAddresses,photos,phoneNumbers,addresses"
            }

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"Failed to get Google profile: {response.text}")

        except Exception as e:
            logger.error(f"Error getting Google user profile: {e}")
            raise

    def get_google_user_emails(self, access_token: str) -> list:
        """
        Get user's email addresses from Google
        Returns list of email addresses
        """
        try:
            profile = self.get_google_user_profile(access_token)
            emails = []

            if "emailAddresses" in profile:
                for email_info in profile["emailAddresses"]:
                    emails.append(
                        {
                            "email": email_info.get("value"),
                            "primary": email_info.get("metadata", {}).get(
                                "primary", False
                            ),
                            "verified": email_info.get("metadata", {}).get(
                                "verified", False
                            ),
                        }
                    )

            return emails

        except Exception as e:
            logger.error(f"Error getting Google user emails: {e}")
            return []

    def check_google_account_status(self, google_user_id: str) -> Dict[str, Any]:
        """
        Check Google account status and permissions
        Returns account status information
        """
        try:
            # This is a placeholder for account status checking
            # In a real implementation, you would:
            # 1. Call Google Admin SDK to check account status
            # 2. Verify account permissions and restrictions
            # 3. Check if account is suspended or disabled

            return {
                "account_status": "active",
                "permissions": ["basic_profile", "email"],
                "restrictions": [],
                "last_checked": time.time(),
            }

        except Exception as e:
            logger.error(f"Error checking Google account status: {e}")
            return {"account_status": "unknown", "error": str(e)}
