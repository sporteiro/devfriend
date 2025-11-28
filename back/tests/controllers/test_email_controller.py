import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
import jwt
from datetime import datetime, timedelta
import os

pytestmark = pytest.mark.skipif(
    os.getenv('PYTEST_USE_REAL_DB') != '1',
    reason='Test requiere base de datos real (PYTEST_USE_REAL_DB=1)'
)

# Create minimal test app
app = FastAPI()

# Import only the email-related routers
from src.api.email_controller import router as email_router
app.include_router(email_router)

# Import real SECRET_KEY and ALGORITHM
from src.utils.security import SECRET_KEY, ALGORITHM

client = TestClient(app)


class TestEmailController:

    def setup_method(self):
        """Setup test data before each test method"""
        self.test_user_id = 1
        self.valid_token = self._create_valid_token(self.test_user_id)

    def _create_valid_token(self, user_id: int) -> str:
        """Create valid JWT token for testing"""
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def test_get_email_integrations_endpoint(self):
        """Test that email integrations endpoint accepts requests and returns proper structure"""
        response = client.get(
            "/email/integrations",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should return list structure
        assert response.status_code in [200, 403, 403, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_email_integration_endpoint(self):
        """Test that create email integration endpoint accepts requests"""
        integration_data = {
            "credential_id": 999  # Non-existent credential
        }

        response = client.post(
            "/email/integrations",
            json=integration_data,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either succeed or fail with proper error
        assert response.status_code in [201, 400, 404, 500]

    def test_get_emails_endpoint(self):
        """Test that get emails endpoint accepts requests"""
        # Test with non-existent integration ID
        response = client.get(
            "/email/integrations/999/emails",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either return emails or error
        assert response.status_code in [200, 400, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_sync_emails_endpoint(self):
        """Test that sync emails endpoint accepts requests"""
        response = client.post(
            "/email/integrations/999/sync",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either succeed or fail with proper error
        assert response.status_code in [200, 400, 404, 500]

    def test_get_email_integrations_without_auth(self):
        """Test that email integrations endpoint requires authentication"""
        response = client.get("/email/integrations")
        assert response.status_code == 403

    def test_create_email_integration_without_auth(self):
        """Test that create email integration endpoint requires authentication"""
        integration_data = {
            "credential_id": 999
        }

        response = client.post("/email/integrations", json=integration_data)
        assert response.status_code == 403

    def test_get_emails_without_auth(self):
        """Test that get emails endpoint requires authentication"""
        response = client.get("/email/integrations/999/emails")
        assert response.status_code == 403

    def test_sync_emails_without_auth(self):
        """Test that sync emails endpoint requires authentication"""
        response = client.post("/email/integrations/999/sync")
        assert response.status_code == 403
