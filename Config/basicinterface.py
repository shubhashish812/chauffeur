"""
Basic Authentication Interface
Handles email/password authentication operations
"""

import logging
from typing import Any, Dict

from Config.models import ChangePasswordData, ResetPasswordData, SigninData, SignupData
from shared.auth_utils import AuthUtils
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

            # Send verification email
            try:
                self.send_verification_email(user_record.uid)
            except Exception as e:
                logger.warning(f"Failed to send verification email: {e}")

            # Create complete user response with tokens
            response_data = self.create_user_response_with_tokens(
                user_record=user_record, provider="email"
            )

            return response_data

        except Exception as e:
            logger.error(f"Error in signup: {e}")
            raise

    def signin(self) -> Dict[str, Any]:
        """
        Authenticate user with email/password
        Returns user data and authentication tokens
        """
        try:
            # Validate data using Pydantic model
            signin_data = SigninData(**self.request_data["data"])

            # Sign in with Firebase REST API
            auth_data = AuthUtils.sign_in_with_password(
                email=signin_data.email, password=signin_data.password
            )

            # Get user record
            user_record = self.get_user_by_email(signin_data.email)

            # Check email verification
            if not user_record.email_verified:
                raise ValueError(
                    "Email verification required. Please check your email and click the verification link."
                )

            # Create complete user response with tokens
            response_data = self.create_user_response_with_tokens(
                user_record=user_record, provider="email"
            )

            # Add Firebase REST API tokens if available (for backward compatibility)
            if "refreshToken" in auth_data:
                response_data["firebase_refresh_token"] = auth_data["refreshToken"]
                response_data["firebase_expires_in"] = auth_data.get("expiresIn")

            return response_data

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
            AuthUtils.exchange_custom_token(custom_token)

            # Send password reset email using Firebase REST API
            api_key = AuthUtils.get_firebase_api_key()
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
