import json
from typing import Any, Dict, List, Optional

from src.models.secret import Secret, SecretCreate, SecretResponse
from src.repositories.secret_repository import SecretRepository


class SecretService:
    def __init__(self, secret_repository: SecretRepository):
        self.secret_repository = secret_repository

    def create_secret(self, user_id: int, data: SecretCreate) -> SecretResponse:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Creating secret for user {user_id}, service_type={data.service_type}, datos_secrets keys: {list(data.datos_secrets.keys()) if isinstance(data.datos_secrets, dict) else 'not a dict'}")
        if isinstance(data.datos_secrets, dict) and 'client_id' in data.datos_secrets:
            logger.debug(f"client_id length: {len(str(data.datos_secrets['client_id']))}, client_secret length: {len(str(data.datos_secrets.get('client_secret', '')))}")
        encrypted_value_str = json.dumps(data.datos_secrets)
        secret = Secret(
            user_id=user_id,
            name=data.name,
            service_type=data.service_type,
            encrypted_value=encrypted_value_str,
        )
        saved = self.secret_repository.save(secret)
        return SecretResponse(**saved.dict())

    def list_secrets(self, user_id: int) -> List[SecretResponse]:
        secrets = self.secret_repository.find_by_user(user_id)
        # Only return safe fields (encrypted_value as '*****')
        return [SecretResponse(**s.dict()) for s in secrets]

    def get_secret(self, user_id: int, secret_id: int) -> Optional[Secret]:
        secret = self.secret_repository.find_by_id(secret_id)
        if secret and secret.user_id == user_id:
            return secret
        return None

    def update_secret(self, user_id: int, secret_id: int, data: Dict[str, Any]) -> Optional[SecretResponse]:
        secret = self.secret_repository.find_by_id(secret_id)
        if not secret or secret.user_id != user_id:
            return None
        if 'datos_secrets' in data:
            secret.encrypted_value = json.dumps(data['datos_secrets'])
        if 'name' in data:
            secret.name = data['name']
        if 'service_type' in data:
            secret.service_type = data['service_type']
        updated = self.secret_repository.save(secret)
        return SecretResponse(**updated.dict())

    def delete_secret(self, user_id: int, secret_id: int) -> bool:
        secret = self.secret_repository.find_by_id(secret_id)
        if secret and secret.user_id == user_id:
            return self.secret_repository.delete(secret_id)
        return False
