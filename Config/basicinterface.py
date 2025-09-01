"""
Basic Authentication Interface
Handles email/password authentication operations
"""

import logging
from typing import Any, Dict

from Config.models import (
    ChangePasswordData,
    ResetPasswordData,
    SigninData,
    SignupData,
    User,
    UserProfile,
    UserRecord,
)
from shared.firebase_client import firebase_client

from .base import BaseAuthInterface

logger = logging.getLogger(__name__)


class BasicAuthInterface(BaseAuthInterface):
    """
    Basic authentication interface for email/password authentication
    Handles user registration, login, and password management
    """

    def __init__(self, request_data: Dict[str, Any]):
        """Initialize basic auth interface"""
        super().__init__(request_data)
        self.request_data = request_data

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def signup(self) -> Dict[str, Any]:
        """
        Register new user with email/password
        Returns user data and authentication tokens

        Response format:
        {
            "uid": "ZY1rJK0eYLg...",
            "email": "[user@example.com]",
            "display_name": "",
            "email_verified": false,
            "provider_data": [],
            "phone_number": null,
            "photo_url": null,
            "disabled": false
        }
        """
        try:
            # Validate data using Pydantic model
            signup_data = SignupData(**self.request_data["data"])

            # Create user in Firebase
            user_properties = {
                "email": signup_data.email,
                "password": signup_data.password,
            }

            if signup_data.display_name:
                user_properties["display_name"] = signup_data.display_name

            user_record = firebase_client.create_user(**user_properties)

            # Create user profile in Firestore
            try:
                user_profile = UserProfile(
                    uid=user_record.uid,
                    name=signup_data.display_name or signup_data.email.split("@")[0],
                    email=signup_data.email,
                    role=signup_data.role,
                    status="offline",  # Default to offline
                    phone_number=user_record.phone_number,
                    photo_url=user_record.photo_url,
                )

                User.sync(doc_id=user_profile.uid, data=user_profile, create=True)
                logger.info(
                    f"Created user profile in Firestore for UID: {user_record.uid}"
                )

            except Exception as e:
                logger.error(f"Failed to create user profile in Firestore: {e}")
                # Don't fail the signup if profile creation fails
                # The user can still authenticate, profile can be created later

            # Send verification email
            try:
                self.send_verification_email(user_record.uid)
            except Exception as e:
                logger.warning(f"Failed to send verification email: {e}")

            return UserRecord.from_firebase_user(user_record).model_dump(mode="json")

        except Exception as e:
            logger.error(f"Error in signup: {e}")
            raise

    def signin(self) -> Dict[str, Any]:
        """
        Authenticate user with email/password
        Returns user data and authentication tokens

        Response format:
        {
            "localId": "ZY1rJK0eYLg...",
            "email": "[user@example.com]",
            "displayName": "",
            "idToken": "[ID_TOKEN]",
            "registered": true,
            "refreshToken": "[REFRESH_TOKEN]",
            "expiresIn": "3600"
        }
        """
        try:
            # Validate data using Pydantic model
            signin_data = SigninData(**self.request_data["data"])

            # Get user record
            user_record = self.get_user_by_email(signin_data.email)

            # Check email verification
            if not user_record.email_verified:
                raise ValueError(
                    "Email verification required. Please check your email and click the verification link."
                )

            # Sign in with Firebase REST API
            auth_data = firebase_client.sign_in_with_password(
                email=signin_data.email, password=signin_data.password
            )

            return auth_data

        except Exception as e:
            logger.error(f"Error in signin: {e}")
            raise

    def signout(self) -> Dict[str, Any]:
        """
        Sign out user and revoke tokens
        Returns success message
        """
        try:
            uid = self.request_data["data"].get("uid")
            if not uid:
                raise ValueError("UID is required for signout")

            success = self.revoke_tokens(uid)

            if success:
                return {"message": "User signed out successfully"}
            else:
                raise ValueError("Failed to sign out user")

        except Exception as e:
            logger.error(f"Error in signout: {e}")
            raise

    def reset_password(self) -> Dict[str, Any]:
        """
        Send password reset email
        Returns success message
        """
        try:
            # Validate data using Pydantic model
            reset_data = ResetPasswordData(**self.request_data["data"])

            # Get user by email
            user_record = self.get_user_by_email(reset_data.email)

            # Create custom token and exchange for ID token
            custom_token = firebase_client.create_custom_token(user_record.uid)
            firebase_client.exchange_custom_token(custom_token)

            # Send password reset email using Firebase REST API
            api_key = firebase_client.get_firebase_api_key()
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"

            payload = {"requestType": "PASSWORD_RESET", "email": reset_data.email}

            import requests

            response = requests.post(url, json=payload)

            if response.status_code == 200:
                logger.info(f"Password reset email sent to {reset_data.email}")
                return {"message": "Password reset email sent successfully"}
            else:
                raise ValueError("Failed to send password reset email")

        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            raise

    def change_password(self) -> Dict[str, Any]:
        """
        Change user password
        Returns success message
        """
        try:
            # Validate data using Pydantic model
            change_data = ChangePasswordData(**self.request_data["data"])

            # Update user password
            firebase_client.update_user(
                change_data.uid, password=change_data.new_password
            )

            # Revoke all refresh tokens to force re-authentication
            self.revoke_tokens(change_data.uid)

            logger.info(f"Password changed successfully for UID {change_data.uid}")
            return {"message": "Password changed successfully"}

        except Exception as e:
            logger.error(f"Error changing password: {e}")
            raise

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
        return "basic"

    def validate_auth_specific_inputs(self, request_data: Dict[str, Any]) -> bool:
        """
        Validate basic auth specific input requirements
        Pydantic models handle validation automatically
        """
        return True

    def get_auth_config(self) -> Dict[str, Any]:
        """
        Get basic auth configuration
        Returns password requirements, 2FA settings, etc.
        """
        return {
            "auth_type": "basic",
            "password_requirements": {
                "min_length": 8,
                "require_uppercase": False,
                "require_lowercase": False,
                "require_numbers": False,
                "require_special_chars": False,
            },
            "email_verification_required": True,
            "two_factor_auth_supported": True,
            "password_reset_enabled": True,
            "supported_actions": [
                "signup",
                "signin",
                "signout",
                "reset_password",
                "change_password",
            ],
        }
