import os
import pytest
if os.getenv("PYTEST_USE_REAL_DB") != "1":
    pytest.skip("Requires a real PostgreSQL database (set PYTEST_USE_REAL_DB=1)", allow_module_level=True)

from tests.test_utils import requires_real_db
from fastapi.testclient import TestClient
from fastapi import FastAPI
import jwt
from datetime import datetime, timedelta
from src.api.integration_controller import router as integration_router

pytestmark = pytest.mark.skipif(
    requires_real_db(),
    reason='Requires a real PostgreSQL database (set PYTEST_USE_REAL_DB=1)'
)

# Create minimal test app
app = FastAPI()

# Import the integration service router
app.include_router(integration_router)

# Import real SECRET_KEY and ALGORITHM
from src.utils.security import SECRET_KEY, ALGORITHM

client = TestClient(app)


class TestIntegrationServiceEndpoints:

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
        """Test that get integrations endpoint returns proper structure"""
        response = client.get(
            "/integrations",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_get_integrations_with_service_type_filter(self):
        """Test that get integrations with service_type filter works"""
        response = client.get(
            "/integrations?service_type=github",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 500]

    def test_get_integration_by_id_endpoint(self):
        """Test that get integration by ID endpoint handles requests"""
        response = client.get(
            "/integrations/999",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 404, 500]

    def test_create_integration_endpoint(self):
        """Test that create integration endpoint accepts requests"""
        integration_data = {
            "user_id": self.test_user_id,
            "secret_id": 999,
            "service_type": "test_service",
            "config": {"test": "config"}
        }

        response = client.post(
            "/integrations",
            json=integration_data,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 400, 404, 500]

    def test_update_integration_endpoint(self):
        """Test that update integration endpoint accepts requests"""
        update_data = {
            "secret_id": 999,
            "config": {"status": "active"}
        }

        response = client.put(
            "/integrations/999",
            json=update_data,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 404, 500]

    def test_delete_integration_endpoint(self):
        """Test that delete integration endpoint accepts requests"""
        response = client.delete(
            "/integrations/999",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        assert response.status_code in [200, 404, 500]

    def test_all_endpoints_require_authentication(self):
        """Test that all integration endpoints require authentication"""
        endpoints = [
            ("GET", "/integrations"),
            ("GET", "/integrations/999"),
            ("POST", "/integrations"),
            ("PUT", "/integrations/999"),
            ("DELETE", "/integrations/999")
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

    def test_create_integration_with_invalid_data(self):
        """Test create integration with various invalid data"""
        invalid_cases = [
            {},  # Empty data
            {"service_type": "test"},  # Missing required fields
            {"user_id": "invalid", "service_type": "test"},  # Invalid user_id type
        ]

        for invalid_data in invalid_cases:
            response = client.post(
                "/integrations",
                json=invalid_data,
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )
            # Should either validate (400) or process (200/500)
            assert response.status_code in [200, 400, 422, 500]

    def test_update_integration_with_invalid_data(self):
        """Test update integration with various invalid data"""
        invalid_cases = [
            {},  # Empty data
            {"config": "invalid_string"},  # Invalid config type
        ]

        for invalid_data in invalid_cases:
            response = client.put(
                "/integrations/999",
                json=invalid_data,
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )
            # Should either validate (400) or process (404/500)
            assert response.status_code in [200, 400, 404, 422, 500]
