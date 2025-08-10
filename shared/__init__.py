"""
Shared utilities for Chauffeur Cloud Functions
"""

from .firebase_client import firebase_client, FirebaseClient
from .auth_utils import AuthUtils
from .models import *

__all__ = [
    'firebase_client',
    'FirebaseClient', 
    'AuthUtils',
    # Models
    'BaseRequest',
    'BaseResponse',
    'ErrorResponse',
    'AuthRequest',
    'SignUpRequest',
    'SignInRequest',
    'OAuthRequest',
    'AuthResponse',
    'UserResponse',
    'UserProfileRequest',
    'UserProfileResponse',
    'UserListResponse',
    'EmailVerificationRequest',
    'EmailVerificationResponse',
    'TokenVerificationRequest',
    'TokenVerificationResponse',
    'TokenRefreshRequest',
    'TokenRefreshResponse',
    'OAuthConfigResponse',
    'OAuthUserResponse',
    'HealthCheckResponse',
    'APIResponse',
    'ValidationError',
    'ValidationErrorResponse',
    'PaginationParams',
    'PaginatedResponse'
]
