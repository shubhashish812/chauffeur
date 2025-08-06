from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from firebase_admin import auth
from typing import Optional, Dict, Any
import requests
import os
import json
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google.auth.exceptions import GoogleAuthError

oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])

# Pydantic models for OAuth requests/responses
class GoogleSignInRequest(BaseModel):
    id_token: str

class OAuthUserResponse(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    email_verified: bool
    provider: str
    provider_uid: Optional[str] = None

class OAuthAuthResponse(BaseModel):
    user: OAuthUserResponse
    token: str

class OAuthProviderConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str

# OAuth Provider configurations
OAUTH_PROVIDERS = {
    "google": {
        "issuer": "https://accounts.google.com",
        "audience": None,  # Will be set from environment
        "user_info_url": "https://www.googleapis.com/oauth2/v3/userinfo"
    }
}

def get_google_client_id() -> str:
    """Get Google OAuth client ID from environment"""
    client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    if not client_id:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth client ID not configured. Set GOOGLE_OAUTH_CLIENT_ID environment variable."
        )
    return client_id

def verify_google_token(id_token_str: str) -> Dict[str, Any]:
    """
    Verify Google ID token and return user information
    """
    try:
        client_id = get_google_client_id()
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            id_token_str, 
            google_requests.Request(), 
            client_id
        )
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return idinfo
        
    except GoogleAuthError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying Google token: {str(e)}")

def get_or_create_firebase_user(provider: str, provider_uid: str, user_info: Dict[str, Any]) -> auth.UserRecord:
    """
    Get existing user or create new user in Firebase Auth
    """
    try:
        # Try to get existing user by email
        user_record = auth.get_user_by_email(user_info['email'])
        
        # Check if user has the same provider linked
        if hasattr(user_record, 'provider_data'):
            for provider_data in user_record.provider_data:
                if provider_data.provider_id == provider and provider_data.uid == provider_uid:
                    return user_record
        
        # If user exists but doesn't have this provider linked, link it
        auth.link_provider_with_uid(
            user_record.uid,
            auth.ProviderConfig(
                provider_id=provider,
                provider_uid=provider_uid
            )
        )
        return user_record
        
    except auth.UserNotFoundError:
        # Create new user
        user_properties = {
            'email': user_info['email'],
            'email_verified': user_info.get('email_verified', False),
            'display_name': user_info.get('name'),
            'photo_url': user_info.get('picture')
        }
        
        # Remove None values
        user_properties = {k: v for k, v in user_properties.items() if v is not None}
        
        user_record = auth.create_user(**user_properties)
        
        # Link the OAuth provider
        auth.link_provider_with_uid(
            user_record.uid,
            auth.ProviderConfig(
                provider_id=provider,
                provider_uid=provider_uid
            )
        )
        
        return user_record
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error managing user: {str(e)}")

@oauth_router.post("/google/signin", response_model=OAuthAuthResponse)
async def google_signin(request: GoogleSignInRequest):
    """
    Sign in with Google OAuth
    """
    try:
        # Verify Google ID token
        google_user_info = verify_google_token(request.id_token)
        
        # Extract user information
        user_info = {
            'email': google_user_info['email'],
            'email_verified': google_user_info.get('email_verified', False),
            'name': google_user_info.get('name'),
            'picture': google_user_info.get('picture')
        }
        
        # Get or create Firebase user
        user_record = get_or_create_firebase_user(
            provider='google.com',
            provider_uid=google_user_info['sub'],
            user_info=user_info
        )
        
        # Create custom token for the user
        custom_token = auth.create_custom_token(user_record.uid)
        
        return OAuthAuthResponse(
            user=OAuthUserResponse(
                uid=user_record.uid,
                email=user_record.email,
                display_name=user_record.display_name,
                email_verified=user_record.email_verified,
                provider='google',
                provider_uid=google_user_info['sub']
            ),
            token=custom_token.decode('utf-8')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during Google signin: {str(e)}")

@oauth_router.get("/google/config")
async def get_google_config():
    """
    Get Google OAuth configuration for frontend
    """
    try:
        client_id = get_google_client_id()
        return {
            "client_id": client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "userinfo_uri": "https://www.googleapis.com/oauth2/v3/userinfo"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Google config: {str(e)}")

# Future OAuth providers can be added here following the same pattern
# Example for future providers:
# @oauth_router.post("/facebook/signin", response_model=OAuthAuthResponse)
# async def facebook_signin(request: FacebookSignInRequest):
#     # Similar implementation for Facebook
#     pass

# @oauth_router.post("/github/signin", response_model=OAuthAuthResponse)
# async def github_signin(request: GitHubSignInRequest):
#     # Similar implementation for GitHub
#     pass
