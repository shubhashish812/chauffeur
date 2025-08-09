from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from firebase_admin import auth
from typing import Optional, Dict, Any
import requests
import os
from .base import BaseAuthProvider, BaseAuthRequest, BaseAuthResponse

class EmailPasswordAuthProvider(BaseAuthProvider):
    """Email/Password authentication provider with email verification"""
    
    def __init__(self):
        self.router = APIRouter(tags=["email-password"])
        super().__init__(self.router)
    
    def setup_routes(self):
        """Setup email/password authentication routes with email verification"""
        class SignUpRequest(BaseAuthRequest):
            email: EmailStr
            password: str
            display_name: Optional[str] = None

        class SignInRequest(BaseAuthRequest):
            email: EmailStr
            password: str

        class UserResponse(BaseModel):
            uid: str
            email: str
            display_name: Optional[str] = None
            email_verified: bool

        class AuthResponse(BaseAuthResponse):
            user: UserResponse

        class VerificationResponse(BaseModel):
            message: str
            email_verified: bool

        @self.router.post("/signup", response_model=AuthResponse)
        async def signup(request: SignUpRequest):
            """Create a new user account with email and password, and send verification email"""
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
                
                # Send email verification automatically
                try:
                    # Use Firebase Auth REST API to send verification email
                    api_key = self.get_environment_variable('FIREBASE_API_KEY', 'Firebase API key')
                    
                    # Get the user's ID token first
                    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
                    payload = {
                        "email": request.email,
                        "password": request.password,
                        "returnSecureToken": True
                    }
                    
                    response = requests.post(url, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        id_token = data['idToken']
                        
                        # Send verification email using REST API
                        verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
                        verify_payload = {
                            "requestType": "VERIFY_EMAIL",
                            "idToken": id_token
                        }
                        
                        verify_response = requests.post(verify_url, json=verify_payload)
                        if verify_response.status_code != 200:
                            print(f"Failed to send verification email: {verify_response.text}")
                    else:
                        print(f"Failed to get ID token for verification email: {response.text}")
                        
                except Exception as e:
                    # Log the error but don't fail the signup
                    print(f"Failed to send verification email: {e}")
                
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

        @self.router.post("/signin", response_model=AuthResponse)
        async def signin(request: SignInRequest):
            """Sign in with email and password using Firebase Auth REST API"""
            try:
                # Get Firebase API key from environment or config
                api_key = self.get_environment_variable('FIREBASE_API_KEY', 'Firebase API key')
                
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

        @self.router.post("/send-verification-email/{uid}", response_model=VerificationResponse)
        async def send_verification_email(uid: str):
            """Send email verification to a user"""
            try:
                # Check if user exists
                user_record = auth.get_user(uid)
                
                # Use Firebase Auth REST API to send verification email
                api_key = self.get_environment_variable('FIREBASE_API_KEY', 'Firebase API key')
                
                # We need to get an ID token for the user to send verification email
                # This is a limitation - we need the user's password or a custom token
                # For now, we'll create a custom token and exchange it for an ID token
                custom_token = auth.create_custom_token(uid)
                
                # Exchange custom token for ID token
                exchange_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}"
                exchange_payload = {
                    "token": custom_token.decode('utf-8'),
                    "returnSecureToken": True
                }
                
                exchange_response = requests.post(exchange_url, json=exchange_payload)
                if exchange_response.status_code == 200:
                    exchange_data = exchange_response.json()
                    id_token = exchange_data['idToken']
                    
                    # Send verification email using REST API
                    verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
                    verify_payload = {
                        "requestType": "VERIFY_EMAIL",
                        "idToken": id_token
                    }
                    
                    verify_response = requests.post(verify_url, json=verify_payload)
                    if verify_response.status_code == 200:
                        return VerificationResponse(
                            message="Verification email sent successfully",
                            email_verified=user_record.email_verified
                        )
                    else:
                        raise HTTPException(status_code=500, detail=f"Failed to send verification email: {verify_response.text}")
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to get ID token: {exchange_response.text}")
                
            except auth.UserNotFoundError:
                raise HTTPException(status_code=404, detail="User not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error sending verification email: {str(e)}")

        @self.router.post("/resend-verification-email", response_model=VerificationResponse)
        async def resend_verification_email(email: str):
            """Resend verification email by email address"""
            try:
                # Get user by email
                user_record = auth.get_user_by_email(email)
                
                # Use Firebase Auth REST API to send verification email
                api_key = self.get_environment_variable('FIREBASE_API_KEY', 'Firebase API key')
                
                # Create custom token and exchange for ID token
                custom_token = auth.create_custom_token(user_record.uid)
                
                # Exchange custom token for ID token
                exchange_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}"
                exchange_payload = {
                    "token": custom_token.decode('utf-8'),
                    "returnSecureToken": True
                }
                
                exchange_response = requests.post(exchange_url, json=exchange_payload)
                if exchange_response.status_code == 200:
                    exchange_data = exchange_response.json()
                    id_token = exchange_data['idToken']
                    
                    # Send verification email using REST API
                    verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
                    verify_payload = {
                        "requestType": "VERIFY_EMAIL",
                        "idToken": id_token
                    }
                    
                    verify_response = requests.post(verify_url, json=verify_payload)
                    if verify_response.status_code == 200:
                        return VerificationResponse(
                            message="Verification email resent successfully",
                            email_verified=user_record.email_verified
                        )
                    else:
                        raise HTTPException(status_code=500, detail=f"Failed to send verification email: {verify_response.text}")
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to get ID token: {exchange_response.text}")
                
            except auth.UserNotFoundError:
                raise HTTPException(status_code=404, detail="User not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error resending verification email: {str(e)}")

        @self.router.get("/check-verification/{uid}", response_model=VerificationResponse)
        async def check_verification_status(uid: str):
            """Check if a user's email is verified"""
            try:
                user_record = auth.get_user(uid)
                
                return VerificationResponse(
                    message="Verification status checked successfully",
                    email_verified=user_record.email_verified
                )
                
            except auth.UserNotFoundError:
                raise HTTPException(status_code=404, detail="User not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error checking verification status: {str(e)}")

        @self.router.post("/require-verification/{uid}")
        async def require_verification(uid: str):
            """Check if user's email is verified and return error if not"""
            try:
                user_record = auth.get_user(uid)
                
                if not user_record.email_verified:
                    raise HTTPException(
                        status_code=403, 
                        detail="Email verification required. Please check your email and click the verification link."
                    )
                
                return {"message": "Email is verified", "email_verified": True}
                
            except auth.UserNotFoundError:
                raise HTTPException(status_code=404, detail="User not found")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error checking verification: {str(e)}")

        @self.router.post("/signout/{uid}")
        async def signout(uid: str):
            """Revoke all refresh tokens for a user (force signout from all devices)"""
            try:
                auth.revoke_refresh_tokens(uid)
                return {"message": "User signed out (tokens revoked) successfully"}
            except auth.UserNotFoundError:
                raise HTTPException(status_code=404, detail="User not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error signing out: {str(e)}")

        @self.router.get("/user/{uid}", response_model=UserResponse)
        async def get_user(uid: str):
            """Get user information by UID"""
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

        @self.router.delete("/user/{uid}")
        async def delete_user(uid: str):
            """Delete a user account"""
            try:
                auth.delete_user(uid)
                return {"message": "User deleted successfully"}
            except auth.UserNotFoundError:
                raise HTTPException(status_code=404, detail="User not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

        @self.router.post("/verify-token")
        async def verify_token(token: str):
            """Verify a Firebase ID token and check if user still exists"""
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

        @self.router.post("/exchange-custom-token")
        async def exchange_custom_token(custom_token: str):
            """Exchange a custom token for an ID token (requires Firebase API key)"""
            try:
                api_key = self.get_environment_variable('FIREBASE_API_KEY', 'Firebase API key')
                
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

        @self.router.post("/refresh-token")
        async def refresh_token(refresh_token: str):
            """Refresh an ID token using a refresh token (requires Firebase API key)"""
            try:
                api_key = self.get_environment_variable('FIREBASE_API_KEY', 'Firebase API key')
                
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

    def authenticate(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user with email/password"""
        # This method is not used for email/password auth as it's handled by individual endpoints
        pass
