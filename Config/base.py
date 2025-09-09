"""
Base Authentication Interface
Abstract base class for all authentication providers
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from firebase_admin.auth import UserRecord

from shared.firebase import firebase_client

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
            return firebase_client.refresh_id_token(refresh_token)
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
            token_data = firebase_client.exchange_custom_token(custom_token)

            # Send verification email
            return firebase_client.send_verification_email(token_data["idToken"])
        except Exception as e:
            logger.error(f"Error sending verification email for UID {uid}: {e}")
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
    def signin(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign in user
        Returns user data + tokens
        """

    @abstractmethod
    def signout(self) -> str:
        """
        Sign out user (revoke tokens ideally)
        Returns success message
        """

    @abstractmethod
    def signup(self, request_data: Dict[str, Any]) -> bool:
        """
        Create new user, trigger email verification if needed
        Returns user data
        """
