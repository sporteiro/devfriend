import os
from typing import List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from src.models.note import Note
from src.repositories.note_repository import NoteRepository


class PostgreSQLNoteRepository(NoteRepository):
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
    ):
        # Usar variables de entorno con valores por defecto para desarrollo
        self.connection_params = {
            "host": host or os.getenv("DB_HOST", "localhost"),
            "port": port or int(os.getenv("DB_PORT", "5432")),
            "database": database or os.getenv("DB_NAME", "devfriend"),
            "user": user or os.getenv("DB_USER", "devfriend"),
            "password": password or os.getenv("DB_PASSWORD", "devfriend"),
        }
        self._create_table()

    def _get_connection(self):
        return psycopg2.connect(**self.connection_params)

    def _create_table(self):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT,
                        user_id INTEGER,
                        is_archived BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """
                )
                conn.commit()
        finally:
            conn.close()

    def save(self, note: Note) -> Note:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if note.id:
                    # Update existing note
                    cursor.execute(
                        """UPDATE notes
                           SET title = %s, content = %s, is_archived = %s
                           WHERE id = %s RETURNING *""",
                        (note.title, note.content, note.is_archived, note.id),
                    )
                else:
                    # Insert new note
                    cursor.execute(
                        """INSERT INTO notes (title, content, user_id, is_archived)
                           VALUES (%s, %s, %s, %s) RETURNING *""",
                        (note.title, note.content, note.user_id, note.is_archived),
                    )
                conn.commit()
                row = cursor.fetchone()
                return Note(**dict(row))
        finally:
            conn.close()

    def find_all(self) -> List[Note]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [Note(**dict(row)) for row in rows]
        finally:
            conn.close()

    def find_by_id(self, note_id: int) -> Optional[Note]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM notes WHERE id = %s", (note_id,))
                row = cursor.fetchone()
                return Note(**dict(row)) if row else None
        finally:
            conn.close()

    def find_by_user(self, user_id: int) -> List[Note]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM notes WHERE user_id = %s ORDER BY created_at DESC",
                    (user_id,),
                )
                rows = cursor.fetchall()
                return [Note(**dict(row)) for row in rows]
        finally:
            conn.close()

    def delete(self, note_id: int) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()
