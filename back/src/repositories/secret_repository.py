from abc import ABC, abstractmethod
from typing import List, Optional

from src.models.secret import Secret


class SecretRepository(ABC):
    @abstractmethod
    def save(self, secret: Secret) -> Secret:
        """Guarda un secret (insert o update)."""
        pass

    @abstractmethod
    def find_by_id(self, secret_id: int) -> Optional[Secret]:
        pass

    @abstractmethod
    def find_by_user(self, user_id: int) -> List[Secret]:
        pass

    @abstractmethod
    def find_all_by_type(self, user_id: int, service_type: str) -> List[Secret]:
        pass

    @abstractmethod
    def delete(self, secret_id: int) -> bool:
        pass
