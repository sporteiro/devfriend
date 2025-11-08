import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta

from src.main import app
from src.utils.security import SECRET_KEY, ALGORITHM

client = TestClient(app)

class TestNoteControllerReal:

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

    def test_get_notes_real(self):
        """Real test that calls API with real authentication"""

        # Make real request with valid token
        response = client.get(
            "/notes",
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )
        # print(f"TOKEN: {self.valid_token}")

        # Verify response
        assert response.status_code == 200
        # Response should be a list (can be empty)
        assert isinstance(response.json(), list)

    def test_create_note_real(self):
        """Real test that creates a note with real authentication"""

        note_data = {
            "title": "Test Note from Real Test",
            "content": "This is a test note created by real API test"
        }

        # Make real request to create note
        response = client.post(
            "/notes",
            json=note_data,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == note_data["title"]
        assert data["content"] == note_data["content"]
        assert data["user_id"] == self.test_user_id

        # Cleanup: delete the created note
        if "id" in data:
            delete_response = client.delete(
                f"/notes/{data['id']}",
                headers={"Authorization": f"Bearer {self.valid_token}"}
            )
            assert delete_response.status_code == 200
