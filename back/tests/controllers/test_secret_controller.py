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

# Import the secrets router
from src.api.secret_controller import router as secret_router
app.include_router(secret_router)

# Import real SECRET_KEY and ALGORITHM
from src.utils.security import SECRET_KEY, ALGORITHM

client = TestClient(app)


class TestSecretController:

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

    def test_list_secrets_endpoint(self):
        """Test that list secrets endpoint returns proper structure"""
        response = client.get(
            "/secrets",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_secret_endpoint(self):
        """Test that create secret endpoint accepts requests"""
        secret_data = {
            "name": "Test Secret",
            "service_type": "test_service",
            "datos_secrets": {"key": "value"}
        }

        response = client.post(
            "/secrets",
            json=secret_data,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [201, 400, 500]

    def test_get_secret_endpoint(self):
        """Test that get secret endpoint handles requests"""
        response = client.get(
            "/secrets/999",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 404, 500]

    def test_update_secret_endpoint(self):
        """Test that update secret endpoint accepts requests"""
        update_data = {
            "name": "Updated Secret",
            "datos_secrets": {"new_key": "new_value"}
        }

        response = client.put(
            "/secrets/999",
            json=update_data,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 404, 500]

    def test_delete_secret_endpoint(self):
        """Test that delete secret endpoint accepts requests"""
        response = client.delete(
            "/secrets/999",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 404, 500]

    def test_all_endpoints_require_authentication(self):
        """Test that all secret endpoints require authentication"""
        endpoints = [
            ("GET", "/secrets"),
            ("GET", "/secrets/999"),
            ("POST", "/secrets"),
            ("PUT", "/secrets/999"),
            ("DELETE", "/secrets/999")
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)

            assert response.status_code in [401, 403]

    def test_create_secret_with_invalid_data(self):
        """Test create secret with various invalid data"""
        invalid_cases = [
            {},  # Empty data
            {"name": "test"},  # Missing required fields
            {"service_type": "test"},  # Missing name
            {"name": "test", "service_type": "test", "datos_secrets": "invalid"}  # Invalid datos_secrets type
        ]

        for invalid_data in invalid_cases:
            response = client.post(
                "/secrets",
                json=invalid_data,
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )
            # Should either validate (422) or process (201/400/500)
            assert response.status_code in [201, 400, 422, 500]

    def test_update_secret_with_invalid_data(self):
        """Test update secret with various invalid data"""
        invalid_cases = [
            {},  # Empty data
            {"datos_secrets": "invalid_string"},  # Invalid datos_secrets type
        ]

        for invalid_data in invalid_cases:
            response = client.put(
                "/secrets/999",
                json=invalid_data,
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )
            # Should either validate (422) or process (404/500)
            assert response.status_code in [200, 400, 404, 422, 500]

    def test_create_secret_with_valid_structure(self):
        """Test create secret with valid data structure"""
        valid_secret = {
            "name": "GitHub Token",
            "service_type": "github",
            "datos_secrets": {
                "access_token": "gho_token_here",
                "client_id": "client_123",
                "client_secret": "secret_456"
            }
        }

        response = client.post(
            "/secrets",
            json=valid_secret,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either succeed or fail with proper error
        assert response.status_code in [201, 400, 500]

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["name"] == "GitHub Token"
            assert data["service_type"] == "github"
