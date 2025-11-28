import pytest
from tests.test_utils import requires_real_db
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI
import jwt
from datetime import datetime, timedelta
from src.api.auth_controller import router as auth_router

pytestmark = pytest.mark.skipif(
    requires_real_db(),
    reason='Requires a real PostgreSQL database (set PYTEST_USE_REAL_DB=1)'
)

# Create minimal test app
app = FastAPI()

# Import only the auth router
app.include_router(auth_router)

# Import real SECRET_KEY and ALGORITHM
from src.utils.security import SECRET_KEY, ALGORITHM


client = TestClient(app)


class TestAuthEndpoints:

    def setup_method(self):
        self.test_user_id = 1
        self.valid_token = self._create_valid_token(self.test_user_id)

    def _create_valid_token(self, user_id: int) -> str:
        """Create valid JWT token for testing"""
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def test_register_endpoint(self):
        """Test register endpoint structure"""
        register_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }

        response = client.post("/auth/register", json=register_data)
        assert response.status_code in [201, 400]

    def test_login_endpoint(self):
        """Test login endpoint structure"""
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }

        response = client.post("/auth/login", json=login_data)
        assert response.status_code in [200, 401]

    def test_get_current_user_endpoint(self):
        """Test current user endpoint structure"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )
        assert response.status_code in [200, 401, 403, 404]
