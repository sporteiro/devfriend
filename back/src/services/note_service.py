from typing import List, Optional

from src.models.note import Note
from src.repositories.note_repository import NoteRepository


class NoteService:
    def __init__(self, note_repository: NoteRepository):
        self.note_repository = note_repository

    def create_note(self, title: str, content: str) -> Note:
        note = Note(title=title, content=content)
        return self.note_repository.save(note)

    def get_all_notes(self) -> List[Note]:
        return self.note_repository.find_all()

    def get_note_by_id(self, note_id: int) -> Optional[Note]:
        return self.note_repository.find_by_id(note_id)

    def update_note(self, note_id: int, title: str, content: str) -> Optional[Note]:
        note = self.note_repository.find_by_id(note_id)
        if note:
            note.title = title
            note.content = content
            return self.note_repository.save(note)
        return None

    def delete_note(self, note_id: int) -> bool:
        return self.note_repository.delete(note_id)
