from fastapi import APIRouter
from .email_password import EmailPasswordAuthProvider
from .google_oauth import GoogleOAuthProvider

# Create unified authentication router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize email/password auth provider
email_password_provider = EmailPasswordAuthProvider()
email_password_provider.setup_routes()

# Create OAuth router
oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])

# Initialize Google OAuth provider
google_oauth_provider = GoogleOAuthProvider()
google_oauth_provider.setup_routes()

# Include OAuth routes in main auth router
auth_router.include_router(oauth_router)

# Export the unified router
__all__ = ['auth_router']
