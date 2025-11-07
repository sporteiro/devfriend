from abc import ABC, abstractmethod
from typing import Optional

from src.models.user import User


class UserRepository(ABC):
    """
    Port (interface) for user persistence.
    Part of hexagonal pattern - defines contract without implementation.
    """

    @abstractmethod
    def save(self, user: User) -> User:
        """Save or update a user."""
        pass

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find a user by ID."""
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update an existing user."""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete a user."""
        pass
