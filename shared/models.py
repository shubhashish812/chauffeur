"""
Shared Pydantic models for Cloud Functions
Consistent request/response schemas across all functions
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime

# Base Models
class BaseRequest(BaseModel):
    """Base request model"""
    pass

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: str
    error_code: Optional[str] = None

# Authentication Models
class AuthRequest(BaseRequest):
    """Base authentication request"""
    email: EmailStr
    password: str = Field(..., min_length=6)

class SignUpRequest(AuthRequest):
    """User registration request"""
    display_name: Optional[str] = None

class SignInRequest(AuthRequest):
    """User login request"""
    pass

class OAuthRequest(BaseRequest):
    """OAuth authentication request"""
    id_token: str

class AuthResponse(BaseResponse):
    """Authentication response"""
    user: Dict[str, Any]
    token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None

class UserResponse(BaseModel):
    """User information response"""
    uid: str
    email: str
    display_name: Optional[str] = None
    email_verified: bool
    provider: Optional[str] = None
    provider_uid: Optional[str] = None
    created_at: Optional[datetime] = None
    last_sign_in: Optional[datetime] = None

# User Management Models
class UserProfileRequest(BaseRequest):
    """User profile update request"""
    display_name: Optional[str] = None
    photo_url: Optional[str] = None

class UserProfileResponse(BaseResponse):
    """User profile response"""
    user: UserResponse

class UserListResponse(BaseResponse):
    """User list response"""
    users: list[UserResponse]
    total: int
    page: int
    limit: int

# Email Verification Models
class EmailVerificationRequest(BaseRequest):
    """Email verification request"""
    uid: str

class EmailVerificationResponse(BaseResponse):
    """Email verification response"""
    email_verified: bool
    message: str

# Token Management Models
class TokenVerificationRequest(BaseRequest):
    """Token verification request"""
    token: str

class TokenVerificationResponse(BaseResponse):
    """Token verification response"""
    valid: bool
    uid: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    user_exists: Optional[bool] = None

class TokenRefreshRequest(BaseRequest):
    """Token refresh request"""
    refresh_token: str

class TokenRefreshResponse(BaseResponse):
    """Token refresh response"""
    id_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"

# OAuth Models
class OAuthConfigResponse(BaseResponse):
    """OAuth configuration response"""
    client_id: str
    auth_uri: str
    token_uri: str
    userinfo_uri: str

class OAuthUserResponse(UserResponse):
    """OAuth user response"""
    provider: str
    provider_uid: str

# Health Check Models
class HealthCheckResponse(BaseResponse):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    environment: str

# API Response Wrapper
class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

# Validation Models
class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    code: Optional[str] = None

class ValidationErrorResponse(BaseResponse):
    """Validation error response"""
    success: bool = False
    errors: list[ValidationError]
    error_type: str = "validation_error"

# Pagination Models
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(default="asc", regex="^(asc|desc)$")

class PaginatedResponse(BaseResponse):
    """Paginated response wrapper"""
    data: list[Dict[str, Any]]
    pagination: Dict[str, Any]
    total: int
    page: int
    limit: int
    total_pages: int
