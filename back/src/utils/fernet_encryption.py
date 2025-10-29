import base64
import os

from cryptography.fernet import Fernet, InvalidToken


class FernetEncryptionAdapter:
    """
    Utilidad para cifrar y descifrar campos sensibles usando Fernet/AES y clave maestra de entorno.
    """
    def __init__(self):
        key = os.getenv('DEVFRIEND_ENCRYPTION_KEY')
        if not key:
            raise ValueError('DEVFRIEND_ENCRYPTION_KEY environment variable is not set')
        if len(key) != 44:
            raise ValueError('Fernet key must be 32 url-safe base64-encoded bytes (44 chars)')
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Cifra un string. Retorna el string cifrado (base64)."""
        token = self.fernet.encrypt(data.encode('utf-8'))
        return token.decode('utf-8')

    def decrypt(self, token: str) -> str:
        """Descifra un string previamente cifrado. Si falla, retorna string vacío."""
        try:
            data = self.fernet.decrypt(token.encode('utf-8'))
            return data.decode('utf-8')
        except InvalidToken:
            return ''
