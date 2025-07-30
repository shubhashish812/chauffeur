from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from firebase_admin import auth
from typing import Optional
import requests
import os

auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models for request/response
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    email_verified: bool

class AuthResponse(BaseModel):
    user: UserResponse
    token: str

@auth_router.post("/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest):
    """
    Create a new user account with email and password
    """
    try:
        # Create user in Firebase Auth
        user_properties = {
            'email': request.email,
            'password': request.password,
            'email_verified': False
        }
        
        if request.display_name:
            user_properties['display_name'] = request.display_name
            
        user_record = auth.create_user(**user_properties)
        
        # Create custom token for the user
        custom_token = auth.create_custom_token(user_record.uid)
        
        return AuthResponse(
            user=UserResponse(
                uid=user_record.uid,
                email=user_record.email,
                display_name=user_record.display_name,
                email_verified=user_record.email_verified
            ),
            token=custom_token.decode('utf-8')
        )
        
    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already exists")
    except ValueError as e:
        if "password" in str(e).lower():
            raise HTTPException(status_code=400, detail="Password is too weak")
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@auth_router.post("/signin", response_model=AuthResponse)
async def signin(request: SignInRequest):
    """
    Sign in with email and password using Firebase Auth REST API
    """
    try:
        # Get Firebase API key from environment or config
        api_key = os.getenv('FIREBASE_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="Firebase API key not configured. Set FIREBASE_API_KEY environment variable."
            )
        
        # Firebase Auth REST API endpoint
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        
        payload = {
            "email": request.email,
            "password": request.password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code != 200:
            error_message = data.get('error', {}).get('message', 'Unknown error')
            if 'EMAIL_NOT_FOUND' in error_message:
                raise HTTPException(status_code=400, detail="Email not found")
            elif 'INVALID_PASSWORD' in error_message:
                raise HTTPException(status_code=400, detail="Invalid password")
            else:
                raise HTTPException(status_code=400, detail=error_message)
        
        # Get user details from Firebase Admin SDK
        user_record = auth.get_user_by_email(request.email)
        
        return AuthResponse(
            user=UserResponse(
                uid=user_record.uid,
                email=user_record.email,
                display_name=user_record.display_name,
                email_verified=user_record.email_verified
            ),
            token=data['idToken']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error signing in: {str(e)}")

@auth_router.post("/signout/{uid}")
async def signout(uid: str):
    """
    Revoke all refresh tokens for a user (force signout from all devices)
    """
    try:
        auth.revoke_refresh_tokens(uid)
        return {"message": "User signed out (tokens revoked) successfully"}
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error signing out: {str(e)}")

@auth_router.get("/user/{uid}", response_model=UserResponse)
async def get_user(uid: str):
    """
    Get user information by UID
    """
    try:
        user_record = auth.get_user(uid)
        return UserResponse(
            uid=user_record.uid,
            email=user_record.email,
            display_name=user_record.display_name,
            email_verified=user_record.email_verified
        )
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

@auth_router.delete("/user/{uid}")
async def delete_user(uid: str):
    """
    Delete a user account
    """
    try:
        auth.delete_user(uid)
        return {"message": "User deleted successfully"}
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@auth_router.post("/verify-token")
async def verify_token(token: str):
    """
    Verify a Firebase ID token and check if user still exists
    """
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        
        # Check if user still exists in Firebase Auth
        try:
            user_record = auth.get_user(uid)
            return {
                "valid": True,
                "uid": uid,
                "email": decoded_token.get('email'),
                "email_verified": decoded_token.get('email_verified', False),
                "user_exists": True
            }
        except auth.UserNotFoundError:
            return {
                "valid": False,
                "uid": uid,
                "error": "User has been deleted",
                "user_exists": False
            }
            
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@auth_router.post("/exchange-custom-token")
async def exchange_custom_token(custom_token: str):
    """
    Exchange a custom token for an ID token (requires Firebase API key)
    """
    try:
        api_key = os.getenv('FIREBASE_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="Firebase API key not configured. Set FIREBASE_API_KEY environment variable."
            )
        
        # Exchange custom token for ID token
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}"
        
        payload = {
            "token": custom_token,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code != 200:
            error_message = data.get('error', {}).get('message', 'Unknown error')
            raise HTTPException(status_code=400, detail=error_message)
        
        return {
            "id_token": data['idToken'],
            "refresh_token": data.get('refreshToken'),
            "expires_in": data.get('expiresIn')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exchanging token: {str(e)}")

@auth_router.post("/refresh-token")
async def refresh_token(refresh_token: str):
    """
    Refresh an ID token using a refresh token (requires Firebase API key)
    """
    try:
        api_key = os.getenv('FIREBASE_API_KEY')
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="Firebase API key not configured. Set FIREBASE_API_KEY environment variable."
            )
        
        # Refresh ID token using refresh token
        url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
        
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code != 200:
            error_message = data.get('error', {}).get('message', 'Unknown error')
            if 'TOKEN_EXPIRED' in error_message:
                raise HTTPException(status_code=401, detail="Refresh token has expired")
            elif 'INVALID_REFRESH_TOKEN' in error_message:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            else:
                raise HTTPException(status_code=400, detail=error_message)
        
        return {
            "id_token": data['id_token'],
            "refresh_token": data.get('refresh_token'),  # New refresh token
            "expires_in": data.get('expires_in'),
            "token_type": data.get('token_type', 'Bearer')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing token: {str(e)}") 