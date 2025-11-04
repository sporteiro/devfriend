import base64
import os

from cryptography.fernet import Fernet, InvalidToken


class FernetEncryptionAdapter:
    """
    Utility to encrypt and decrypt sensitive fields using Fernet/AES and master key from environment.
    """
    def __init__(self):
        key = os.getenv('DEVFRIEND_ENCRYPTION_KEY')
        if not key:
            raise ValueError('DEVFRIEND_ENCRYPTION_KEY environment variable is not set')
        if len(key) != 44:
            raise ValueError('Fernet key must be 32 url-safe base64-encoded bytes (44 chars)')
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt a string. Returns the encrypted string (base64)."""
        token = self.fernet.encrypt(data.encode('utf-8'))
        return token.decode('utf-8')

    def decrypt(self, token: str) -> str:
        """Decrypt a previously encrypted string. If it fails, returns empty string."""
        try:
            data = self.fernet.decrypt(token.encode('utf-8'))
            return data.decode('utf-8')
        except InvalidToken:
            return ''
