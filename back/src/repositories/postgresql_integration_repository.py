import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from src.utils.get_db_config import GetDBConfig


class PostgreSQLIntegrationRepository:
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
    ):
        base_config = GetDBConfig().get_db_config()
        self.connection_params = {
            "host": host or base_config["host"],
            "port": port or base_config["port"],
            "database": database or base_config["database"],
            "user": user or base_config["user"],
            "password": password or base_config["password"],
        }
        self._create_table()

    def _get_connection(self):
        return psycopg2.connect(**self.connection_params)

    def _create_table(self):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS integrations (
                        id SERIAL,
                        user_id INTEGER NOT NULL,
                        secret_id INTEGER,
                        service_type VARCHAR(100) NOT NULL,
                        config JSONB,
                        is_active BOOLEAN NOT NULL DEFAULT true,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(id)
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_integrations_user
                    ON integrations (user_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_integrations_secret
                    ON integrations (secret_id)
                """)
                conn.commit()
        finally:
            conn.close()

    def fetch_all(self, query: str, *params) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            conn.close()

    def fetch_one(self, query: str, *params) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def execute(self, query: str, *params) -> None:
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
        finally:
            conn.close()
