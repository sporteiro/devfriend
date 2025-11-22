import os


class GetDBConfig:
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "postgres"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "devfriend"),
            "user": os.getenv("DB_USER", "devfriend"),
            "password": os.getenv("DB_PASSWORD", "devfriend"),
        }
    def get_db_config(self):
        return self.db_config
