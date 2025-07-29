import firebase_admin
from firebase_admin import credentials, initialize_app
import os

# Path to your service account key JSON file
SERVICE_ACCOUNT_KEY_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY', 'serviceAccountKey.json')

firebase_app = None

def init_firebase():
    global firebase_app
    if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
        raise FileNotFoundError(f"Firebase service account key not found at {SERVICE_ACCOUNT_KEY_PATH}. Set the FIREBASE_SERVICE_ACCOUNT_KEY environment variable or place the key at the default location.")
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            firebase_app = initialize_app(cred)
        else:
            firebase_app = firebase_admin.get_app()
        return firebase_app
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        raise