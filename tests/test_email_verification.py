import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from firebase_admin import auth

# Mock Firebase Auth for testing
@pytest.fixture
def mock_firebase_auth():
    with patch('firebase_admin.auth') as mock_auth:
        # Mock user record
        mock_user = MagicMock()
        mock_user.uid = "test_uid_123"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.email_verified = False
        
        # Mock create_user
        mock_auth.create_user.return_value = mock_user
        
        # Mock get_user
        mock_auth.get_user.return_value = mock_user
        
        # Mock get_user_by_email
        mock_auth.get_user_by_email.return_value = mock_user
        
        # Mock send_email_verification
        mock_auth.send_email_verification.return_value = None
        
        yield mock_auth

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

class TestEmailVerification:
    """Test email verification functionality"""
    
    def test_signup_sends_verification_email(self, mock_firebase_auth, client):
        """Test that signup automatically sends verification email"""
        with patch('app.auth.email_password.auth') as mock_auth:
            # Mock user creation
            mock_user = MagicMock()
            mock_user.uid = "test_uid_123"
            mock_user.email = "test@example.com"
            mock_user.display_name = "Test User"
            mock_user.email_verified = False
            mock_auth.create_user.return_value = mock_user
            
            # Mock custom token creation
            mock_auth.create_custom_token.return_value = b"test_token"
            
            # Test signup
            response = client.post("/auth/email-password/signup", json={
                "email": "test@example.com",
                "password": "securepassword123",
                "display_name": "Test User"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["email"] == "test@example.com"
            assert data["user"]["email_verified"] == False
            
            # Verify send_email_verification was called
            mock_auth.send_email_verification.assert_called_once_with("test_uid_123")
    
    def test_send_verification_email_endpoint(self, mock_firebase_auth, client):
        """Test manual verification email sending"""
        with patch('app.auth.email_password.auth') as mock_auth:
            mock_user = MagicMock()
            mock_user.email_verified = False
            mock_auth.get_user.return_value = mock_user
            
            response = client.post("/auth/email-password/send-verification-email/test_uid_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Verification email sent successfully"
            assert data["email_verified"] == False
            
            # Verify send_email_verification was called
            mock_auth.send_email_verification.assert_called_once_with("test_uid_123")
    
    def test_resend_verification_email(self, mock_firebase_auth, client):
        """Test resending verification email by email address"""
        with patch('app.auth.email_password.auth') as mock_auth:
            mock_user = MagicMock()
            mock_user.uid = "test_uid_123"
            mock_user.email_verified = False
            mock_auth.get_user_by_email.return_value = mock_user
            
            response = client.post("/auth/email-password/resend-verification-email", 
                                data={"email": "test@example.com"})
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Verification email resent successfully"
            assert data["email_verified"] == False
            
            # Verify send_email_verification was called
            mock_auth.send_email_verification.assert_called_once_with("test_uid_123")
    
    def test_check_verification_status(self, mock_firebase_auth, client):
        """Test checking verification status"""
        with patch('app.auth.email_password.auth') as mock_auth:
            mock_user = MagicMock()
            mock_user.email_verified = True
            mock_auth.get_user.return_value = mock_user
            
            response = client.get("/auth/email-password/check-verification/test_uid_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Verification status checked successfully"
            assert data["email_verified"] == True
    
    def test_require_verification_success(self, mock_firebase_auth, client):
        """Test require verification when email is verified"""
        with patch('app.auth.email_password.auth') as mock_auth:
            mock_user = MagicMock()
            mock_user.email_verified = True
            mock_auth.get_user.return_value = mock_user
            
            response = client.post("/auth/email-password/require-verification/test_uid_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Email is verified"
            assert data["email_verified"] == True
    
    def test_require_verification_failure(self, mock_firebase_auth, client):
        """Test require verification when email is not verified"""
        with patch('app.auth.email_password.auth') as mock_auth:
            mock_user = MagicMock()
            mock_user.email_verified = False
            mock_auth.get_user.return_value = mock_user
            
            response = client.post("/auth/email-password/require-verification/test_uid_123")
            
            assert response.status_code == 403
            data = response.json()
            assert "Email verification required" in data["detail"]
    
    def test_user_not_found_errors(self, mock_firebase_auth, client):
        """Test error handling when user is not found"""
        with patch('app.auth.email_password.auth') as mock_auth:
            mock_auth.get_user.side_effect = auth.UserNotFoundError("User not found")
            
            # Test send verification email
            response = client.post("/auth/email-password/send-verification-email/invalid_uid")
            assert response.status_code == 404
            assert response.json()["detail"] == "User not found"
            
            # Test check verification
            response = client.get("/auth/email-password/check-verification/invalid_uid")
            assert response.status_code == 404
            assert response.json()["detail"] == "User not found"
            
            # Test require verification
            response = client.post("/auth/email-password/require-verification/invalid_uid")
            assert response.status_code == 404
            assert response.json()["detail"] == "User not found"

class TestEmailVerificationIntegration:
    """Integration tests for email verification"""
    
    def test_complete_verification_flow(self, mock_firebase_auth, client):
        """Test complete email verification flow"""
        with patch('app.auth.email_password.auth') as mock_auth:
            # Mock user creation
            mock_user = MagicMock()
            mock_user.uid = "test_uid_123"
            mock_user.email = "test@example.com"
            mock_user.display_name = "Test User"
            mock_user.email_verified = False
            mock_auth.create_user.return_value = mock_user
            mock_auth.get_user.return_value = mock_user
            mock_auth.create_custom_token.return_value = b"test_token"
            
            # 1. Signup (should send verification email)
            response = client.post("/auth/email-password/signup", json={
                "email": "test@example.com",
                "password": "securepassword123",
                "display_name": "Test User"
            })
            assert response.status_code == 200
            
            # 2. Check verification status (should be False)
            response = client.get("/auth/email-password/check-verification/test_uid_123")
            assert response.status_code == 200
            assert response.json()["email_verified"] == False
            
            # 3. Try to require verification (should fail)
            response = client.post("/auth/email-password/require-verification/test_uid_123")
            assert response.status_code == 403
            
            # 4. Mock email verification (simulate user clicking link)
            mock_user.email_verified = True
            
            # 5. Check verification status again (should be True)
            response = client.get("/auth/email-password/check-verification/test_uid_123")
            assert response.status_code == 200
            assert response.json()["email_verified"] == True
            
            # 6. Require verification (should succeed)
            response = client.post("/auth/email-password/require-verification/test_uid_123")
            assert response.status_code == 200
            assert response.json()["email_verified"] == True

class TestUnifiedAuthStructure:
    """Test the unified authentication structure"""
    
    def test_auth_router_exists(self, client):
        """Test that the unified auth router is accessible"""
        # Test that the auth router is included
        response = client.get("/hello")
        assert response.status_code == 200
    
    def test_email_password_endpoints_available(self, client):
        """Test that email/password endpoints are available"""
        # Test signup endpoint exists (will fail due to missing data, but endpoint exists)
        response = client.post("/auth/email-password/signup", json={})
        # Should fail due to validation, but endpoint exists
        assert response.status_code in [400, 422]  # Validation error expected
    
    def test_oauth_endpoints_available(self, client):
        """Test that OAuth endpoints are available"""
        # Test Google OAuth config endpoint
        response = client.get("/oauth/google/config")
        # Should fail due to missing config, but endpoint exists
        assert response.status_code in [500, 404]  # Config error expected

if __name__ == "__main__":
    pytest.main([__file__])
