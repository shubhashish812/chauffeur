"""
Shared utilities for Chauffeur Cloud Functions
"""

from .firebase import FirebaseClient, firebase_client

__all__ = ["firebase_client", "FirebaseClient"]
