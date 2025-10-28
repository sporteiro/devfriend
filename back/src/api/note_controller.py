import os
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status

from src.middleware.auth_middleware import get_current_user_id
from src.models.note import Note
from src.repositories.postgresql_repository import PostgreSQLNoteRepository
from src.services.note_service import NoteService

# Cargar variables de entorno desde .env
load_dotenv()

router = APIRouter()

# Configuración de PostgreSQL desde variables de entorno
db_config = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "devfriend"),
    "user": os.getenv("DB_USER", "devfriend"),
    "password": os.getenv("DB_PASSWORD", "devfriend"),
}

note_service = NoteService(PostgreSQLNoteRepository(**db_config))


@router.get("/notes", response_model=List[Note])
async def get_notes(user_id: int = Depends(get_current_user_id)):
    """Obtiene todas las notas del usuario autenticado."""
    return note_service.get_notes_by_user(user_id)


@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_note(note: Note, user_id: int = Depends(get_current_user_id)):
    """Crea una nueva nota para el usuario autenticado."""
    return note_service.create_note(note.title, note.content, user_id=user_id)


@router.get("/notes/{note_id}", response_model=Note)
async def get_note(note_id: int, user_id: int = Depends(get_current_user_id)):
    """Obtiene una nota específica del usuario autenticado."""
    note = note_service.get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    # Verificar que la nota pertenece al usuario
    if note.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return note


@router.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: int, note: Note, user_id: int = Depends(get_current_user_id)):
    """Actualiza una nota del usuario autenticado."""
    existing_note = note_service.get_note_by_id(note_id)
    if not existing_note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    # Verificar que la nota pertenece al usuario
    if existing_note.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    updated_note = note_service.update_note(note_id, note.title, note.content)
    return updated_note


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int, user_id: int = Depends(get_current_user_id)):
    """Elimina una nota del usuario autenticado."""
    note = note_service.get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    # Verificar que la nota pertenece al usuario
    if note.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    note_service.delete_note(note_id)
    return {"message": "Note deleted successfully"}
