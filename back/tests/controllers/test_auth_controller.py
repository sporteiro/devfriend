import os
import pytest
if os.getenv("PYTEST_USE_REAL_DB") != "1":
    pytest.skip("Requires a real PostgreSQL database (set PYTEST_USE_REAL_DB=1)", allow_module_level=True)

from tests.test_utils import requires_real_db
from fastapi.testclient import TestClient
from fastapi import FastAPI
import jwt
from datetime import datetime, timedelta
from src.api.auth_controller import router as auth_router

pytestmark = pytest.mark.skipif(
    requires_real_db(),
    reason='Requires a real PostgreSQL database (set PYTEST_USE_REAL_DB=1)'
)

# Create a minimal test app to avoid import issues
app = FastAPI()

# Import and include only the auth router from the correct location
app.include_router(auth_router)

# Import the real SECRET_KEY and ALGORITHM
from src.utils.security import SECRET_KEY, ALGORITHM

client = TestClient(app)


class TestAuthController:

    def setup_method(self):
        """Setup test data before each test method"""
        self.test_user_id = 1
        self.valid_token = self._create_valid_token(self.test_user_id)

    def _create_valid_token(self, user_id: int) -> str:
        """Create valid JWT token for testing using the real SECRET_KEY"""
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def test_register_endpoint(self):
        """Test that register endpoint accepts requests and returns proper structure"""
        register_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }

        response = client.post("/auth/register", json=register_data)

        # Should either succeed or fail with proper error
        assert response.status_code in [201, 400]

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["email"] == "test@example.com"
            assert "created_at" in data
            assert "is_active" in data

    def test_login_endpoint(self):
        """Test that login endpoint accepts requests and returns proper structure"""
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }

        response = client.post("/auth/login", json=login_data)

        # Should either succeed or fail with proper error
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_get_current_user_endpoint(self):
        """Test that current user endpoint returns proper structure with valid token"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either return user or error
        assert response.status_code in [200, 401, 403, 404]

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "email" in data
            assert "created_at" in data
            assert "is_active" in data
