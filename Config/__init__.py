from .basicinterface import BasicAuthInterface
from .googleauthinterface import GoogleAuthInterface
from .models import BasicAuthData, GoogleAuthData

AUTH_REGISTRY = {
    "google": (GoogleAuthInterface, GoogleAuthData),
    "basic": (BasicAuthInterface, BasicAuthData),
}
