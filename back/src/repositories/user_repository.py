from abc import ABC, abstractmethod
from typing import Optional

from src.models.user import User


class UserRepository(ABC):
    """
    Puerto (interfaz) para persistencia de usuarios.
    Parte del patrón hexagonal - define el contrato sin implementación.
    """

    @abstractmethod
    def save(self, user: User) -> User:
        """Guarda o actualiza un usuario."""
        pass

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Busca un usuario por ID."""
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """Busca un usuario por email."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Actualiza un usuario existente."""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Elimina un usuario."""
        pass

