import os
import json

# Path to your Google OAuth client credentials JSON file
GOOGLE_OAUTH_CREDS_PATH = os.getenv('GOOGLE_OAUTH_CREDS_PATH', '../oauthClientCreds.json')


def init_google_oauth():
    """
    Loads the Google OAuth client ID from the credentials file and sets the
    GOOGLE_OAUTH_CLIENT_ID environment variable if not already set.
    """
    if os.getenv('GOOGLE_OAUTH_CLIENT_ID'):
        return os.getenv('GOOGLE_OAUTH_CLIENT_ID')

    if not os.path.exists(GOOGLE_OAUTH_CREDS_PATH):
        raise FileNotFoundError(f"Google OAuth client credentials not found at {GOOGLE_OAUTH_CREDS_PATH}. Set the GOOGLE_OAUTH_CREDS_PATH environment variable or place the file at the default location.")

    with open(GOOGLE_OAUTH_CREDS_PATH, 'r') as f:
        creds = json.load(f)

    # Extract client_id from the JSON path web.client_id
    client_id = creds.get('web', {}).get('client_id')
    if not client_id:
        raise ValueError(f"client_id not found in {GOOGLE_OAUTH_CREDS_PATH} at path web.client_id")

    os.environ['GOOGLE_OAUTH_CLIENT_ID'] = client_id
    return client_id
