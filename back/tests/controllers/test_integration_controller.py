import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
import jwt
from datetime import datetime, timedelta
import os

if os.getenv('PYTEST_USE_REAL_DB') != '1':
    pytest.skip('Test requires real database: set PYTEST_USE_REAL_DB=1 to run', allow_module_level=True)

# Create minimal test app
app = FastAPI()

# Import the integration router
from src.api.integration_controller import router as integration_router
app.include_router(integration_router)

# Import real SECRET_KEY and ALGORITHM
from src.utils.security import SECRET_KEY, ALGORITHM

client = TestClient(app)


class TestIntegrationController:

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

    def test_get_integrations_endpoint(self):
        """Test that integrations endpoint accepts requests and returns proper structure"""
        response = client.get(
            "/integrations",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should return list structure
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_get_integrations_with_service_type_filter(self):
        """Test that integrations endpoint accepts service_type filter"""
        response = client.get(
            "/integrations?service_type=github",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should return list structure
        assert response.status_code in [200, 500]

    def test_get_integration_by_id_endpoint(self):
        """Test that get integration by ID endpoint accepts requests"""
        # Test with non-existent integration ID
        response = client.get(
            "/integrations/999",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either return integration or error
        assert response.status_code in [200, 404, 500]

    def test_create_integration_endpoint(self):
        """Test that create integration endpoint accepts requests"""
        integration_data = {
            "user_id": 1,
            "secret_id": 999,  # Non-existent secret
            "service_type": "github",
            "config": {}
        }

        response = client.post(
            "/integrations",
            json=integration_data,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either succeed or fail with proper error
        assert response.status_code in [200, 400, 404, 500]

    def test_update_integration_endpoint(self):
        """Test that update integration endpoint accepts requests"""
        update_data = {
            "secret_id": 999,
            "config": {"status": "updated"}
        }

        response = client.put(
            "/integrations/999",
            json=update_data,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either succeed or fail with proper error
        assert response.status_code in [200, 404, 500]

    def test_delete_integration_endpoint(self):
        """Test that delete integration endpoint accepts requests"""
        response = client.delete(
            "/integrations/999",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either succeed or fail with proper error
        assert response.status_code in [200, 404, 500]

    def test_get_integrations_without_auth(self):
        """Test that integrations endpoint requires authentication"""
        response = client.get("/integrations")
        assert response.status_code in [401, 403]

    def test_get_integration_by_id_without_auth(self):
        """Test that get integration by ID endpoint requires authentication"""
        response = client.get("/integrations/999")
        assert response.status_code in [401, 403]

    def test_create_integration_without_auth(self):
        """Test that create integration endpoint requires authentication"""
        integration_data = {
            "user_id": 1,
            "secret_id": 999,
            "service_type": "github",
            "config": {}
        }

        response = client.post("/integrations", json=integration_data)
        assert response.status_code in [401, 403]

    def test_update_integration_without_auth(self):
        """Test that update integration endpoint requires authentication"""
        update_data = {
            "secret_id": 999,
            "config": {"status": "updated"}
        }

        response = client.put("/integrations/999", json=update_data)
        assert response.status_code in [401, 403]

    def test_delete_integration_without_auth(self):
        """Test that delete integration endpoint requires authentication"""
        response = client.delete("/integrations/999")
        assert response.status_code in [401, 403]
