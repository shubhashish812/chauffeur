from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from firebase_admin import auth
from typing import Optional, Dict, Any
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google.auth.exceptions import GoogleAuthError
from .base import BaseAuthProvider, BaseAuthRequest, BaseAuthResponse

class GoogleOAuthProvider(BaseAuthProvider):
    """Google OAuth authentication provider"""
    
    def setup_routes(self):
        """Setup Google OAuth authentication routes"""
        
        # Pydantic models for Google OAuth
        class GoogleSignInRequest(BaseAuthRequest):
            id_token: str

        class OAuthUserResponse(BaseModel):
            uid: str
            email: str
            display_name: Optional[str] = None
            email_verified: bool
            provider: str
            provider_uid: Optional[str] = None

        class OAuthAuthResponse(BaseAuthResponse):
            user: OAuthUserResponse

        @self.router.post("/google/signin", response_model=OAuthAuthResponse)
        async def google_signin(request: GoogleSignInRequest):
            """Sign in with Google OAuth"""
            try:
                # Verify Google ID token
                google_user_info = self.verify_google_token(request.id_token)
                
                # Extract user information
                user_info = {
                    'email': google_user_info['email'],
                    'email_verified': google_user_info.get('email_verified', False),
                    'display_name': google_user_info.get('name'),
                    'photo_url': google_user_info.get('picture')
                }
                
                # Get or create Firebase user
                user_record = self.get_or_create_firebase_user(
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

        @self.router.get("/google/config")
        async def get_google_config():
            """Get Google OAuth configuration for frontend"""
            try:
                client_id = self.get_google_client_id()
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

    def get_google_client_id(self) -> str:
        """Get Google OAuth client ID from environment"""
        return self.get_environment_variable('GOOGLE_OAUTH_CLIENT_ID', 'Google OAuth client ID')

    def verify_google_token(self, id_token_str: str) -> Dict[str, Any]:
        """Verify Google ID token and return user information"""
        try:
            client_id = self.get_google_client_id()
            
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

    def get_or_create_firebase_user(self, provider: str, provider_uid: str, user_info: Dict[str, Any]) -> auth.UserRecord:
        """Get existing user or create new user in Firebase Auth"""
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
                'display_name': user_info.get('display_name'),
                'photo_url': user_info.get('photo_url')
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

    def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user with Google OAuth"""
        id_token = credentials.get('id_token')
        if not id_token:
            raise HTTPException(status_code=400, detail="Google ID token is required")
        
        google_user_info = self.verify_google_token(id_token)
        
        user_info = {
            'email': google_user_info['email'],
            'email_verified': google_user_info.get('email_verified', False),
            'display_name': google_user_info.get('name'),
            'photo_url': google_user_info.get('picture')
        }
        
        user_record = self.get_or_create_firebase_user(
            provider='google.com',
            provider_uid=google_user_info['sub'],
            user_info=user_info
        )
        
        custom_token = auth.create_custom_token(user_record.uid)
        
        return self.create_auth_response(user_record, custom_token.decode('utf-8'), 'google')
