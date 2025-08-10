from .models import (
    BasicAuthData, SignupData, SigninData, ResetPasswordData, ChangePasswordData,
    GoogleAuthData, AuthRequest
)
from .basicinterface import BasicAuthInterface
from .googleauthinterface import GoogleAuthInterface

AUTH_REGISTRY = {
    "google": (GoogleAuthInterface, GoogleAuthData),
    "basic": (BasicAuthInterface, BasicAuthData)
}






