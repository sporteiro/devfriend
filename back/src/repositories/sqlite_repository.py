import sqlite3
from typing import List, Optional
from src.models.note import Note
from src.repositories.note_repository import NoteRepository


class SQLiteNoteRepository(NoteRepository):
    def __init__(self, db_path: str = "devfriend.db"):
        self.db_path = db_path
        self._create_table()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_table(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def save(self, note: Note) -> Note:
        with self._get_connection() as conn:
            if note.id:
                # Update existing note
                conn.execute(
                    "UPDATE notes SET title = ?, content = ? WHERE id = ?",
                    (note.title, note.content, note.id)
                )
            else:
                # Insert new note
                cursor = conn.execute(
                    "INSERT INTO notes (title, content) VALUES (?, ?)",
                    (note.title, note.content)
                )
                note.id = cursor.lastrowid
            conn.commit()
            return note
    
    def find_all(self) -> List[Note]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM notes ORDER BY created_at DESC").fetchall()
            return [Note(**dict(row)) for row in rows]
    
    def find_by_id(self, note_id: int) -> Optional[Note]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
            return Note(**dict(row)) if row else None
    
    def delete(self, note_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0
