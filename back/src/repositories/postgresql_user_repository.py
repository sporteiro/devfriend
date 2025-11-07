from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from src.models.user import User
from src.repositories.user_repository import UserRepository


class PostgreSQLUserRepository(UserRepository):
    """
    Secondary adapter for user persistence in PostgreSQL.
    Implements the UserRepository port.
    """

    def __init__(
        self,
        host: str = "postgres",
        port: int = 5432,
        database: str = "devfriend",
        user: str = "devfriend",
        password: str = "devfriend",
    ):
        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
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
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        password_hash VARCHAR(256) NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN NOT NULL DEFAULT TRUE
                    )
                """
                )
                conn.commit()
        finally:
            conn.close()

    def save(self, user: User) -> User:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if user.id:
                    # Update
                    cursor.execute(
                        """
                        UPDATE users
                        SET email = %s, password_hash = %s,
                            updated_at = %s, is_active = %s
                        WHERE id = %s
                        RETURNING *
                    """,
                        (
                            user.email,
                            user.password_hash,
                            datetime.now(),
                            user.is_active,
                            user.id,
                        ),
                    )
                else:
                    # Insert
                    cursor.execute(
                        """
                        INSERT INTO users (email, password_hash, is_active)
                        VALUES (%s, %s, %s)
                        RETURNING *
                    """,
                        (user.email, user.password_hash, user.is_active),
                    )

                conn.commit()
                row = cursor.fetchone()
                return User(**dict(row))
        finally:
            conn.close()

    def find_by_id(self, user_id: int) -> Optional[User]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cursor.fetchone()
                return User(**dict(row)) if row else None
        finally:
            conn.close()

    def find_by_email(self, email: str) -> Optional[User]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                row = cursor.fetchone()
                return User(**dict(row)) if row else None
        finally:
            conn.close()

    def update(self, user: User) -> User:
        return self.save(user)

    def delete(self, user_id: int) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()
