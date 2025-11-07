import pytest

from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import status

from src.main import app


@pytest.fixture
def mock_note_service():
    """Mock the NoteService used in the notes router."""
    with patch("src.routes.note_router.note_service") as mock:
        yield mock


@pytest.mark.asyncio
async def test_get_notes(mock_note_service):
    mock_note_service.get_notes_by_user.return_value = [
        {"id": 1, "title": "Test Note", "content": "Some text", "user_id": 123}
    ]

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/notes", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["title"] == "Test Note"
    mock_note_service.get_notes_by_user.assert_called_once()


@pytest.mark.asyncio
async def test_create_note(mock_note_service):
    mock_note_service.create_note.return_value = {
        "id": 1,
        "title": "New Note",
        "content": "Hello",
        "user_id": 123,
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/notes",
            json={"title": "New Note", "content": "Hello"},
            headers={"Authorization": "Bearer faketoken"},
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == "New Note"
    mock_note_service.create_note.assert_called_once()


@pytest.mark.asyncio
async def test_get_note_authorized(mock_note_service):
    mock_note_service.get_note_by_id.return_value = type(
        "Note", (), {"id": 1, "title": "A", "content": "B", "user_id": 123}
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/notes/1", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "A"


@pytest.mark.asyncio
async def test_get_note_not_found(mock_note_service):
    mock_note_service.get_note_by_id.return_value = None

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/notes/999", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_note(mock_note_service):
    note_mock = type("Note", (), {"id": 1, "user_id": 123})
    mock_note_service.get_note_by_id.return_value = note_mock

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete("/notes/1", headers={"Authorization": "Bearer faketoken"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Note deleted successfully"
    mock_note_service.delete_note.assert_called_once_with(1)
