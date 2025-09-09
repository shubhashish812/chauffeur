"""
Google OAuth Authentication Interface
Handles Google OAuth authentication operations
"""

import logging
from typing import Any, Dict

from Config.models import GoogleAuthData, User, UserProfile, UserRecord
from shared.firebase import firebase_client

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

            existing_profile = User.get(user_record.uid)

            if not existing_profile:
                # Create new user profile for first-time Google sign-in
                # Note: Role will need to be set separately since it's not in Google data
                logger.info(f"First-time Google sign-in for UID: {user_record.uid}")
                # You might want to redirect user to complete profile setup
                # For now, we'll create a basic profile with role as "rider" (default)

                try:
                    user_profile = UserProfile(
                        uid=user_record.uid,
                        name=user_record.display_name
                        or user_record.email.split("@")[0],
                        email=user_record.email,
                        role="rider",  # Default role - can be updated later
                        status="offline",
                        phone_number=user_record.phone_number,
                        photo_url=user_record.photo_url,
                    )

                    User.sync(doc_id=user_profile.uid, data=user_profile, create=True)
                    logger.info(
                        f"Created user profile for Google OAuth user: {user_record.uid}"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to create user profile for Google OAuth user: {e}"
                    )
                    # Don't fail the signin if profile creation fails

            return UserRecord.from_firebase_user(user_record).model_dump(mode="json")

        except Exception as e:
            logger.error(f"Error in Google OAuth signin: {e}")
            raise
