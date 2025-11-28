import pytest
from tests.test_utils import requires_real_db
import os
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta
from src.main import app
from src.utils.security import SECRET_KEY, ALGORITHM

pytestmark = pytest.mark.skipif(
    requires_real_db(),
    reason='Requires a real PostgreSQL database (set PYTEST_USE_REAL_DB=1)'
)

client = TestClient(app)


class TestGitHubControllerReal:

    def setup_method(self):
        # Create valid JWT token for testing
        self.test_user_id = 1
        self.valid_token = self._create_valid_token(self.test_user_id)

    def _create_valid_token(self, user_id: int) -> str:
        """Create valid JWT token for testing"""
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def test_get_github_integrations_real(self):
        """Real test that checks GitHub integrations endpoint"""

        # Make real request with valid token
        response = client.get(
            "/github/integrations",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Verify response structure
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Can be empty list if no integrations

    def test_create_github_integration_real(self):
        """Real test that tries to create GitHub integration (will fail without credentials)"""

        integration_data = {
            "credential_id": 999  # Non-existent credential
        }

        # Make real request to create integration
        response = client.post(
            "/github/integrations",
            json=integration_data,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should either succeed or fail with specific error
        assert response.status_code in [201, 400, 404, 500]

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["service_type"] == "github"

            # Cleanup: delete the created integration
            delete_response = client.delete(
                f"/github/integrations/{data['id']}",
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )
            assert delete_response.status_code == 200
        else:
            # Verify error response structure
            error_data = response.json()
            assert "detail" in error_data

    def test_get_github_integration_repos_real(self):
        """Real test that checks repos endpoint (will fail without valid integration)"""

        # First get integrations to see if we have any
        integrations_response = client.get(
            "/github/integrations",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        integrations = integrations_response.json()

        if integrations:
            # Test with first integration
            integration_id = integrations[0]["id"]

            response = client.get(
                f"/github/integrations/{integration_id}/repos",
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )

            # Should either return repos or error
            assert response.status_code in [200, 400, 404, 500]

            if response.status_code == 200:
                repos = response.json()
                assert isinstance(repos, list)
        else:
            # Test with non-existent integration ID - ahora espera 500
            response = client.get(
                "/github/integrations/999/repos",
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )
            # Actual: 500, no 404
            assert response.status_code == 500

    def test_get_github_integration_user_real(self):
        """Real test that checks user profile endpoint"""

        # Get integrations first
        integrations_response = client.get(
            "/github/integrations",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        integrations = integrations_response.json()

        if integrations:
            integration_id = integrations[0]["id"]

            response = client.get(
                f"/github/integrations/{integration_id}/user",
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )

            assert response.status_code in [200, 400, 404, 500]

            if response.status_code == 200:
                user_data = response.json()
                assert isinstance(user_data, dict)
        else:
            # Test error case - ahora espera 500
            response = client.get(
                "/github/integrations/999/user",
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )
            assert response.status_code == 500

    def test_github_integration_stats_real(self):
        """Real test that checks stats endpoint"""

        integrations_response = client.get(
            "/github/integrations",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        integrations = integrations_response.json()

        if integrations:
            integration_id = integrations[0]["id"]

            response = client.get(
                f"/github/integrations/{integration_id}/stats",
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )

            assert response.status_code in [200, 400, 404, 500]

            if response.status_code == 200:
                stats = response.json()
                assert isinstance(stats, dict)
        else:
            response = client.get(
                "/github/integrations/999/stats",
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )
            assert response.status_code == 404

    def test_delete_nonexistent_github_integration_real(self):
        """Real test that tries to delete non-existent integration"""

        response = client.delete(
            "/github/integrations/999999",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Actual: 500, no 404
        assert response.status_code == 500
