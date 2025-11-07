from typing import Optional

from src.models.user import User, UserCreate, UserLogin
from src.repositories.user_repository import UserRepository
from src.utils.security import create_access_token, hash_password, verify_password


class AuthService:
    """
    Application service for authentication (hexagonal layer).
    Orchestrates business logic for registration, login and validation.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.
        Raises exception if email already exists.
        """
        # Check if user already exists
        existing_user = self.user_repository.find_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash the password
        password_hash = hash_password(user_data.password)

        # Create user
        new_user = User(email=user_data.email, password_hash=password_hash)

        # Save to repository
        return self.user_repository.save(new_user)

    def login_user(self, credentials: UserLogin) -> Optional[str]:
        """
        Authenticate a user and return a JWT token.
        Returns None if credentials are invalid.
        """
        # Find user by email
        user = self.user_repository.find_by_email(credentials.email)
        if not user:
            return None

        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            return None

        # Verify that the user is active
        if not user.is_active:
            return None

        # Generate JWT token
        token_data = {"sub": str(user.id), "email": user.email}
        token = create_access_token(token_data)

        return token

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return self.user_repository.find_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return self.user_repository.find_by_email(email)
