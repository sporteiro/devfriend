from fastapi import APIRouter, HTTPException
from typing import List
from src.models.note import Note
from src.services.note_service import NoteService
from src.repositories.sqlite_repository import SQLiteNoteRepository


router = APIRouter()
note_service = NoteService(SQLiteNoteRepository())

@router.get("/notes", response_model=List[Note])
async def get_notes():
    return note_service.get_all_notes()

@router.post("/notes", response_model=Note)
async def create_note(note: Note):
    return note_service.create_note(note.title, note.content)

@router.get("/notes/{note_id}", response_model=Note)
async def get_note(note_id: int):
    note = note_service.get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: int, note: Note):
    updated_note = note_service.update_note(note_id, note.title, note.content)
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")
    return updated_note

@router.delete("/notes/{note_id}")
async def delete_note(note_id: int):
    if not note_service.delete_note(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}
