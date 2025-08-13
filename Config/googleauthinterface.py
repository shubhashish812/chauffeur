"""
Google OAuth Authentication Interface
Handles Google OAuth authentication operations
"""

import logging
from typing import Any, Dict

from Config.models import GoogleAuthData, UserRecord
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
            google_data = GoogleAuthData(**self.request_data["data"])
            user_record = firebase_client.get_user_from_token(google_data.id_token)
            return UserRecord.from_firebase_user(user_record)

        except Exception as e:
            logger.error(f"Error in Google OAuth signin: {e}")
            raise
