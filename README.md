## Getting Started

### 1. Setting up WSL (Windows Subsystem for Linux)

1. Open **PowerShell as Administrator** and run:
   ```powershell
   wsl --install
   ```
   - This installs WSL and Ubuntu by default. If prompted, restart your computer.
2. Open **Ubuntu** from the Start menu OR if prompted during the installation itself and set up your Linux username and password.

### 2. Installing make and Python venv in WSL

1. In your Ubuntu/WSL terminal, run:
   ```sh
   sudo apt update
   sudo apt install make python3.12-venv
   ```

### 3. (Optional) Remove sudo password prompt for your user

1. In your WSL terminal, run:
   ```sh
   sudo visudo
   ```
2. Add this line at the end (replace `yourusername` with your Linux username, check with `whoami`):
   ```
   yourusername ALL=(ALL) NOPASSWD:ALL
   ```
3. Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X` if using nano).

### 4. Project Setup and Usage

1. Navigate to your project directory (replace with your actual path):
   ```sh
   cd /mnt/c/Users/YourName/WorkSpace/chauffeur
   ```
2. Create and activate a virtual environment:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install all dependencies inside the virtual environment:
   ```sh
   make install (OR use the pip directly)
   pip install -r requirements-dev.txt
   ```
4. Start the development server:
   ```sh
   make start
   ```
5. Build the Docker image:
   ```sh
   make build-dev
   ```
6. Run the Docker container:
   ```sh
   make run-dev
   ```

---

## Authentication

The application uses a scalable authentication architecture with a base class system that supports multiple authentication providers.

### Architecture Overview

```
app/auth/
├── base.py              # Base authentication provider class
├── email_password.py    # Email/password authentication provider
├── google_oauth.py      # Google OAuth authentication provider
└── __init__.py          # Package exports
```

### Email/Password Authentication

The application supports traditional email/password authentication:

- **Sign Up**: `POST /auth/signup`
- **Sign In**: `POST /auth/signin`
- **Sign Out**: `POST /auth/signout/{uid}`
- **Get User**: `GET /auth/user/{uid}`
- **Delete User**: `DELETE /auth/user/{uid}`
- **Verify Token**: `POST /auth/verify-token`
- **Exchange Custom Token**: `POST /auth/exchange-custom-token`
- **Refresh Token**: `POST /auth/refresh-token`

### Google OAuth Authentication

The application supports Google OAuth for seamless authentication:

#### Setup Instructions

See the detailed setup guide in [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)

#### Quick Setup

1. **Get Google OAuth Client ID**:
   - Follow the guide in `GOOGLE_OAUTH_SETUP.md`
   - Or use the quick steps below

2. **Set Environment Variables**:
   ```bash
   export GOOGLE_OAUTH_CLIENT_ID="your-google-client-id"
   export FIREBASE_API_KEY="your-firebase-api-key"
   ```

3. **API Endpoints**:
   - **Google Sign In**: `POST /oauth/google/signin`
   - **Get Google Config**: `GET /oauth/google/config`

#### Frontend Integration Example

```javascript
// Initialize Google Sign-In
function initializeGoogleSignIn() {
  google.accounts.id.initialize({
    client_id: 'YOUR_GOOGLE_CLIENT_ID',
    callback: handleCredentialResponse
  });
}

// Handle the credential response
async function handleCredentialResponse(response) {
  try {
    const result = await fetch('/oauth/google/signin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id_token: response.credential
      })
    });
    
    const data = await result.json();
    // Store the token and user info
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
  } catch (error) {
    console.error('Google sign-in failed:', error);
  }
}
```

### Scalable Architecture

The authentication system is designed to be scalable and easily extensible:

- **Base Class System**: All auth providers inherit from `BaseAuthProvider`
- **Provider-Agnostic**: The system can accommodate multiple OAuth providers
- **Unified User Management**: All users (email/password and OAuth) are stored in Firebase Auth
- **Consistent API**: All authentication methods return the same response format
- **Easy Extension**: Adding new providers follows the same pattern

#### Adding New OAuth Providers

To add new OAuth providers (Facebook, GitHub, etc.):

1. Create a new provider class in `app/auth/` (e.g., `facebook_oauth.py`)
2. Inherit from `BaseAuthProvider`
3. Implement the required methods (`setup_routes`, `authenticate`)
4. Add the provider to `app/auth_router.py`
5. Follow the same pattern as Google OAuth

Example:
```python
class FacebookOAuthProvider(BaseAuthProvider):
    def setup_routes(self):
        # Implement Facebook OAuth routes
        pass
    
    def authenticate(self, credentials):
        # Implement Facebook authentication
        pass
```

---

- Root endpoint: `/`
- Example endpoint: `/hello` 