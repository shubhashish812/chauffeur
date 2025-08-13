"""
Shared Firebase client for Cloud Functions
Handles initialization and common Firebase operations
"""

import logging
import os
from typing import Any, Dict, Optional

import firebase_admin
import requests
from firebase_admin import auth, credentials, exceptions, firestore

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

    # =========================================================================
    # ENVIRONMENT CONSTRUCTOR METHODS
    # =========================================================================

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                # In Cloud Functions, use default credentials
                # The service account is automatically available
                if os.getenv("GOOGLE_CLOUD_PROJECT") and os.getenv(
                    "GOOGLE_APPLICATION_CREDENTIALS"
                ):
                    cred = credentials.Certificate(
                        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                    )
                    firebase_admin.initialize_app(
                        cred, {"projectId": os.getenv("GOOGLE_CLOUD_PROJECT")}
                    )
                    logger.info(
                        "Firebase Admin SDK initialized locally with service account"
                    )
                else:
                    firebase_admin.initialize_app()
                    logger.info(
                        "Firebase Admin SDK initialized with default credentials"
                    )
            else:
                logger.info("Firebase Admin SDK already initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            # Don't raise the exception, just log it
            # This allows the function to start even if Firebase fails
            logger.warning("Continuing without Firebase initialization")

    def get_firestore(self, database_id: str = "chauffeur"):
        """Get Firestore client"""
        return firestore.client(database_id=database_id)

    def get_firebase_api_key(self) -> str:
        """Get Firebase API key from environment"""
        api_key = os.getenv("FIREBASE_API_KEY")
        if not api_key:
            raise ValueError("FIREBASE_API_KEY environment variable not set")
        return api_key

    def get_google_client_id(self) -> str:
        """Get Google OAuth client ID from environment"""
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        if not client_id:
            raise ValueError("GOOGLE_OAUTH_CLIENT_ID environment variable not set")
        return client_id

    # =========================================================================
    # USER MANAGEMENT METHODS
    # =========================================================================

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

        except ValueError as e:
            logger.error(f"Invalid arguments: {e}")
            raise
        except exceptions.FirebaseError as e:
            logger.error(f"Error creating user: {e.http_response} {e.code}: {e.cause}")
            raise

    def get_user_by_email(self, email: str) -> auth.UserRecord:
        """Get user by email"""
        try:
            return auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            logger.warning(f"User not found: {email}")
            raise
        except exceptions.FirebaseError as e:
            logger.error(
                f"Error getting user by email: {e.http_response} {e.code}: {e.cause}"
            )
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

    # =========================================================================
    # BASIC AUTH UTILITY METHODS
    # =========================================================================

    def sign_in_with_password(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with email/password using Firebase REST API"""
        try:
            api_key = self.get_firebase_api_key()
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

            payload = {"email": email, "password": password, "returnSecureToken": True}

            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error signing in with password: {e}")
            raise

    def get_user_from_token(self, token: str) -> auth.UserRecord:
        """Get user record from Firebase ID token"""
        try:
            decoded_token = self.verify_id_token(token)
            uid = decoded_token["uid"]
            return self.get_user(uid)
        except Exception as e:
            logger.error(f"Error getting user from token: {e}")
            raise

    # =========================================================================
    # GOOGLE AUTH UTILITY METHODS
    # =========================================================================

    def verify_google_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Google ID token"""
        try:
            from google.auth.exceptions import GoogleAuthError
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token

            client_id = self.get_google_client_id()

            idinfo = google_id_token.verify_oauth2_token(
                id_token, google_requests.Request(), client_id
            )

            if idinfo["iss"] not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                raise ValueError("Wrong issuer.")

            return idinfo

        except GoogleAuthError as e:  # type: ignore[name-defined]
            logger.error(f"Google auth error: {e}")
            raise ValueError(f"Invalid Google token: {str(e)}")
        except ValueError as e:
            logger.error(f"Token verification failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error verifying Google token: {e}")
            raise

    # =========================================================================
    # TOKEN MANAGEMENT METHODS
    # =========================================================================

    def send_verification_email(self, id_token: str) -> bool:
        """Send email verification using Firebase REST API"""
        try:
            api_key = self.get_firebase_api_key()
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

    def exchange_custom_token(self, custom_token: str) -> Dict[str, Any]:
        """Exchange custom token for ID token"""
        try:
            api_key = self.get_firebase_api_key()
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

    def refresh_id_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh ID token using refresh token"""
        try:
            api_key = self.get_firebase_api_key()
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


# Global instance
firebase_client = FirebaseClient()
