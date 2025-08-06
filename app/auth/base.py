from abc import ABC, abstractmethod
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from firebase_admin import auth
from typing import Optional, Dict, Any
import os

class BaseAuthProvider(ABC):
    """Base class for all authentication providers"""
    
    def __init__(self, router: APIRouter):
        self.router = router
        self.setup_routes()
    
    @abstractmethod
    def setup_routes(self):
        """Setup the routes for this auth provider"""
        pass
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user with the provider"""
        pass
    
    def create_firebase_user(self, user_info: Dict[str, Any]) -> auth.UserRecord:
        """Create or get existing user in Firebase Auth"""
        try:
            # Try to get existing user by email
            user_record = auth.get_user_by_email(user_info['email'])
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
            
            return auth.create_user(**user_properties)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error managing user: {str(e)}")
    
    def create_auth_response(self, user_record: auth.UserRecord, token: str, provider: str = None) -> Dict[str, Any]:
        """Create standardized auth response"""
        return {
            "user": {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified,
                "provider": provider
            },
            "token": token
        }
    
    def get_environment_variable(self, var_name: str, description: str = None) -> str:
        """Get environment variable with proper error handling"""
        value = os.getenv(var_name)
        if not value:
            raise HTTPException(
                status_code=500,
                detail=f"{description or var_name} not configured. Set {var_name} environment variable."
            )
        return value

# Base Pydantic models
class BaseAuthRequest(BaseModel):
    """Base class for authentication requests"""
    pass

class BaseAuthResponse(BaseModel):
    """Base class for authentication responses"""
    user: Dict[str, Any]
    token: str
