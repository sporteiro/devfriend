import json
import os
from typing import List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from src.models.secret import Secret
from src.repositories.secret_repository import SecretRepository
from src.utils.fernet_encryption import FernetEncryptionAdapter


class PostgreSQLSecretRepository(SecretRepository):
    def __init__(self, host: str = "postgres", port: int = 5432, database: str = "devfriend", user: str = "devfriend", password: str = "devfriend"):
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.crypto = FernetEncryptionAdapter()
        self._create_table()

    def _get_connection(self):
        return psycopg2.connect(**self.connection_params)

    def _create_table(self):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS secrets (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        name VARCHAR(150) NOT NULL,
                        encrypted_value TEXT NOT NULL,
                        service_type VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_secrets_user ON secrets(user_id);
                    """
                )
                conn.commit()
        finally:
            conn.close()

    def save(self, secret: Secret) -> Secret:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                encrypted_value = self.crypto.encrypt(secret.encrypted_value)
                if secret.id:
                    cursor.execute(
                        """
                        UPDATE secrets SET name=%s, encrypted_value=%s, service_type=%s,
                            updated_at=NOW()
                        WHERE id=%s RETURNING *
                        """,
                        (secret.name, encrypted_value, secret.service_type, secret.id)
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO secrets (user_id, name, encrypted_value, service_type)
                        VALUES (%s, %s, %s, %s)
                        RETURNING *
                        """,
                        (secret.user_id, secret.name, encrypted_value, secret.service_type)
                    )
                conn.commit()
                row = cursor.fetchone()
                if row:
                    return Secret(**row)
                return secret
        finally:
            conn.close()

    def find_by_id(self, secret_id: int) -> Optional[Secret]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM secrets WHERE id=%s", (secret_id,))
                row = cursor.fetchone()
                if row:
                    # solo desciframos el encrypted_value, nunca lo exponemos
                    row['encrypted_value'] = self.crypto.decrypt(row['encrypted_value'])
                    return Secret(**row)
                return None
        finally:
            conn.close()

    def find_by_user(self, user_id: int) -> List[Secret]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM secrets WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
                rows = cursor.fetchall()
                secrets = []
                for row in rows:
                    row['encrypted_value'] = '*****'  # nunca devolvemos valor real
                    secrets.append(Secret(**row))
                return secrets
        finally:
            conn.close()

    def find_all_by_type(self, user_id: int, service_type: str) -> List[Secret]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM secrets WHERE user_id=%s AND service_type=%s ORDER BY created_at DESC", (user_id, service_type))
                rows = cursor.fetchall()
                secrets = []
                for row in rows:
                    row['encrypted_value'] = '*****'
                    secrets.append(Secret(**row))
                return secrets
        finally:
            conn.close()

    def delete(self, secret_id: int) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM secrets WHERE id=%s", (secret_id,))
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()
