# Firebase Email Verification System Guide

This guide explains how to use the Firebase email verification system implemented in your Chauffeur application.

## Overview

The email verification system automatically sends verification emails when users sign up with email/password authentication. It provides several endpoints to manage the verification process.

## Features

- ✅ **Automatic verification email** on user signup
- ✅ **Manual verification email sending** by UID or email
- ✅ **Verification status checking**
- ✅ **Verification requirement enforcement**
- ✅ **Resend verification email** functionality

## API Endpoints

### 1. Signup with Automatic Verification Email

**Endpoint:** `POST /auth/email-password/signup`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "display_name": "John Doe"
}
```

**Response:**
```json
{
  "user": {
    "uid": "user123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "email_verified": false
  },
  "token": "custom_token_here"
}
```

**Note:** Verification email is automatically sent after successful signup.

### 2. Send Verification Email

**Endpoint:** `POST /auth/email-password/send-verification-email/{uid}`

**Response:**
```json
{
  "message": "Verification email sent successfully",
  "email_verified": false
}
```

### 3. Resend Verification Email by Email Address

**Endpoint:** `POST /auth/email-password/resend-verification-email`

**Request Body:** `email=user@example.com`

**Response:**
```json
{
  "message": "Verification email resent successfully",
  "email_verified": false
}
```

### 4. Check Verification Status

**Endpoint:** `GET /auth/email-password/check-verification/{uid}`

**Response:**
```json
{
  "message": "Verification status checked successfully",
  "email_verified": true
}
```

### 5. Require Email Verification

**Endpoint:** `POST /auth/email-password/require-verification/{uid}`

**Response (if verified):**
```json
{
  "message": "Email is verified",
  "email_verified": true
}
```

**Response (if not verified):**
```json
{
  "detail": "Email verification required. Please check your email and click the verification link."
}
```

## Firebase Configuration

### 1. Enable Email Verification in Firebase Console

1. Go to Firebase Console → Authentication → Settings
2. Enable "Email verification" in the "User actions" section
3. Configure your email templates (optional)

### 2. Email Templates (Optional)

You can customize email templates in Firebase Console:

1. Go to Authentication → Templates
2. Select "Verification email"
3. Customize the subject, content, and styling

### 3. Action URL Configuration

Configure the action URL in Firebase Console:

1. Go to Authentication → Settings → Authorized domains
2. Add your domain (e.g., `localhost:8000` for development)
3. Set the action URL to redirect users after verification

## Usage Examples

### Frontend Integration

```javascript
// Signup with automatic verification
const signup = async (email, password, displayName) => {
  const response = await fetch('/auth/email-password/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, display_name: displayName })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Show message to check email
    alert('Please check your email for verification link');
    return data;
  }
};

// Check verification status
const checkVerification = async (uid) => {
  const response = await fetch(`/auth/email-password/check-verification/${uid}`);
  const data = await response.json();
  return data.email_verified;
};

// Require verification before sensitive actions
const performSensitiveAction = async (uid) => {
  try {
    await fetch(`/auth/email-password/require-verification/${uid}`, {
      method: 'POST'
    });
    // Proceed with sensitive action
  } catch (error) {
    // Handle verification requirement
    alert('Please verify your email first');
  }
};
```

### Backend Integration

```python
# Example: Require verification for sensitive operations
from fastapi import Depends, HTTPException
from app.auth.email_password import EmailPasswordAuthProvider

async def require_email_verification(uid: str):
    """Dependency to require email verification"""
    try:
        # This will raise HTTPException if email is not verified
        await EmailPasswordAuthProvider().require_verification(uid)
        return True
    except HTTPException:
        raise HTTPException(
            status_code=403,
            detail="Email verification required for this operation"
        )

# Use in your routes
@app.post("/sensitive-operation")
async def sensitive_operation(
    uid: str,
    verified: bool = Depends(require_email_verification)
):
    # Only executed if email is verified
    return {"message": "Operation completed"}
```

## Error Handling

### Common Error Responses

1. **User Not Found (404):**
```json
{
  "detail": "User not found"
}
```

2. **Email Verification Required (403):**
```json
{
  "detail": "Email verification required. Please check your email and click the verification link."
}
```

3. **Email Already Exists (400):**
```json
{
  "detail": "Email already exists"
}
```

## Security Considerations

1. **Rate Limiting:** Consider implementing rate limiting for verification email endpoints
2. **Token Expiration:** Verification links expire after a certain time (configurable in Firebase)
3. **Domain Restrictions:** Configure authorized domains in Firebase Console
4. **Email Templates:** Use custom templates to prevent phishing

## Testing

### Test Email Verification Flow

1. **Signup a new user**
2. **Check email for verification link**
3. **Click the verification link**
4. **Verify status using check endpoint**
5. **Test sensitive operations with verification requirement**

### Development Testing

For development, you can:
1. Use Firebase Emulator Suite
2. Configure test email addresses
3. Use Firebase Console to manually verify emails

## Troubleshooting

### Common Issues

1. **Verification emails not sending:**
   - Check Firebase Console settings
   - Verify service account permissions
   - Check email quotas

2. **Verification links not working:**
   - Check authorized domains in Firebase Console
   - Verify action URL configuration
   - Check if links are expired

3. **Users can't verify:**
   - Check email templates
   - Verify email delivery
   - Check spam folders

### Debug Steps

1. Check Firebase Console logs
2. Monitor email delivery in Firebase Console
3. Test with different email providers
4. Verify domain configuration

## Environment Variables

Make sure these environment variables are set:

```bash
FIREBASE_SERVICE_ACCOUNT_KEY=path/to/serviceAccountKey.json
FIREBASE_API_KEY=your_firebase_api_key
```

## Next Steps

1. **Customize email templates** in Firebase Console
2. **Implement rate limiting** for verification endpoints
3. **Add verification requirement** to sensitive operations
4. **Set up monitoring** for email delivery
5. **Configure custom domains** for production
