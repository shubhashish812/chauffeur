from fastapi import APIRouter
from .basic_auth import EmailPasswordAuthProvider
from .google_oauth import GoogleOAuthProvider

# Create main router (no prefix - will be added by main app)
main_router = APIRouter()

# Initialize email/password auth provider
email_password_provider = EmailPasswordAuthProvider()

# Initialize Google OAuth provider
google_oauth_provider = GoogleOAuthProvider()

# Include email-password routes under /auth prefix
auth_router = APIRouter(prefix="/auth", tags=["authentication"])
auth_router.include_router(email_password_provider.router)

# Include OAuth routes under /oauth prefix
oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])
oauth_router.include_router(google_oauth_provider.router)

# Include both routers in main router
main_router.include_router(auth_router)
main_router.include_router(oauth_router)

# Export the main router
__all__ = ['main_router']
