"""
Shared Firebase client for Cloud Functions
Handles initialization and common Firebase operations
"""

import logging
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth, firestore

logger = logging.getLogger(__name__)


class FirebaseClient:
    """Singleton Firebase client for Cloud Functions"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                # In Cloud Functions, use default credentials
                # The service account is automatically available
                firebase_admin.initialize_app()
                logger.info(
                    "Firebase Admin SDK initialized successfully with default credentials"
                )
            else:
                logger.info("Firebase Admin SDK already initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            # Don't raise the exception, just log it
            # This allows the function to start even if Firebase fails
            logger.warning("Continuing without Firebase initialization")

    def get_auth(self):
        """Get Firebase Auth client"""
        return auth

    def get_firestore(self, database_id: str = "chauffeur"):
        """Get Firestore client"""
        return firestore.client(database_id=database_id)

    def create_user(
        self, email: str, password: str, display_name: Optional[str] = None
    ) -> auth.UserRecord:
        """Create a new user in Firebase Auth"""
        try:
            user_properties = {
                "email": email,
                "password": password,
                "email_verified": False,
            }

            if display_name:
                user_properties["display_name"] = display_name

            user_record = auth.create_user(**user_properties)
            logger.info(f"Created user: {user_record.uid}")
            return user_record

        except auth.EmailAlreadyExistsError:
            logger.warning(f"Email already exists: {email}")
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    def get_user_by_email(self, email: str) -> auth.UserRecord:
        """Get user by email"""
        try:
            return auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            logger.warning(f"User not found: {email}")
            raise
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise

    def get_user(self, uid: str) -> auth.UserRecord:
        """Get user by UID"""
        try:
            return auth.get_user(uid)
        except auth.UserNotFoundError:
            logger.warning(f"User not found: {uid}")
            raise
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise

    def create_custom_token(self, uid: str) -> str:
        """Create custom token for user"""
        try:
            token = auth.create_custom_token(uid)
            return token.decode("utf-8")
        except Exception as e:
            logger.error(f"Error creating custom token: {e}")
            raise

    def verify_id_token(self, token: str) -> Dict[str, Any]:
        """Verify Firebase ID token"""
        try:
            return auth.verify_id_token(token)
        except Exception as e:
            logger.error(f"Error verifying ID token: {e}")
            raise

    def delete_user(self, uid: str):
        """Delete user by UID"""
        try:
            auth.delete_user(uid)
            logger.info(f"Deleted user: {uid}")
        except auth.UserNotFoundError:
            logger.warning(f"User not found for deletion: {uid}")
            raise
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise

    def revoke_refresh_tokens(self, uid: str):
        """Revoke all refresh tokens for user"""
        try:
            auth.revoke_refresh_tokens(uid)
            logger.info(f"Revoked refresh tokens for user: {uid}")
        except auth.UserNotFoundError:
            logger.warning(f"User not found for token revocation: {uid}")
            raise
        except Exception as e:
            logger.error(f"Error revoking refresh tokens: {e}")
            raise


# Global instance
firebase_client = FirebaseClient()
