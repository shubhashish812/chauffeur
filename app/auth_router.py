from fastapi import APIRouter
from .auth import EmailPasswordAuthProvider, GoogleOAuthProvider

# Create the main auth router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize email/password auth provider
email_password_provider = EmailPasswordAuthProvider(auth_router)

# Create OAuth router
oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])

# Initialize Google OAuth provider
google_oauth_provider = GoogleOAuthProvider(oauth_router)

# Export both routers
__all__ = ['auth_router', 'oauth_router']
