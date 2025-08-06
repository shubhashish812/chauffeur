# Google OAuth Setup Guide

This guide will walk you through setting up Google OAuth for your Chauffeur application.

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on "Select a project" at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "Chauffeur App")
5. Click "Create"

## Step 2: Enable the Google+ API

1. In your Google Cloud project, go to "APIs & Services" → "Library"
2. Search for "Google+ API" or "Google Identity"
3. Click on "Google Identity" or "Google+ API"
4. Click "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in the required information (App name, User support email, Developer contact information)
   - Add scopes: `email`, `profile`, `openid`
   - Add test users if needed
   - Save and continue

4. Create the OAuth 2.0 Client ID:
   - Application type: "Web application"
   - Name: "Chauffeur Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:3000` (for development)
     - `http://localhost:8000` (for your FastAPI server)
     - Add your production domain when ready
   - Authorized redirect URIs:
     - `http://localhost:3000/auth/callback`
     - `http://localhost:8000/auth/callback`
     - Add your production callback URL when ready
   - Click "Create"

5. **Copy the Client ID** - You'll need this for the next step

## Step 4: Set Environment Variables

Set the following environment variables in your system:
```bash
# For Windows PowerShell:
$env:GOOGLE_OAUTH_CLIENT_ID="your-client-id-here"
$env:FIREBASE_API_KEY="your-firebase-api-key"

# For Linux/Mac:
export GOOGLE_OAUTH_CLIENT_ID="your-client-id-here"
export FIREBASE_API_KEY="your-firebase-api-key"
```

## Step 5: Update the HTML Example

In the `tests/oauth_example.html` file, replace `YOUR_GOOGLE_CLIENT_ID` with your actual client ID:

```html
<div id="g_id_onload"
     data-client_id="123456789-abcdefghijklmnop.apps.googleusercontent.com"
     data-callback="handleCredentialResponse"
     data-auto_prompt="false">
</div>
```

## Step 6: Test the Setup

1. Start your FastAPI server:
   ```bash
   make start
   ```

2. Open the HTML example in your browser:
   ```
   file:///C:\Users\shubh\OneDrive\Documents\WorkSpace\chauffeur\tests\oauth_example.html
   ```

3. Click the "Sign in with Google" button and test the authentication

## Troubleshooting

### Common Issues:

1. **"Invalid client" error**: Make sure your Client ID is correct and the domain is authorized
2. **"Redirect URI mismatch"**: Add your domain to the authorized redirect URIs in Google Cloud Console
3. **"Origin not allowed"**: Add your domain to the authorized JavaScript origins

### Security Notes:

- Never commit your Client ID to version control
- Use environment variables for sensitive configuration
- Add `.env` files to your `.gitignore`
- For production, use HTTPS and proper domain names

## Production Deployment

When deploying to production:

1. Update the authorized origins and redirect URIs in Google Cloud Console
2. Use HTTPS for all URLs
3. Set up proper environment variables on your server
4. Consider using a secrets management service

## Additional OAuth Providers

To add other OAuth providers (Facebook, GitHub, etc.):

1. Create a new provider class in `app/auth/` (e.g., `facebook_oauth.py`)
2. Inherit from `BaseAuthProvider`
3. Implement the required methods
4. Add the provider to `app/auth_router.py`
5. Follow the same pattern as Google OAuth

Example for Facebook:
```python
class FacebookOAuthProvider(BaseAuthProvider):
    def setup_routes(self):
        # Implement Facebook OAuth routes
        pass
    
    def authenticate(self, credentials):
        # Implement Facebook authentication
        pass
```
