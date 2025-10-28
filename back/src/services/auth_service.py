from typing import Optional

from src.models.user import User, UserCreate, UserLogin
from src.repositories.user_repository import UserRepository
from src.utils.security import create_access_token, hash_password, verify_password


class AuthService:
    """
    Servicio de aplicación para autenticación (capa hexagonal).
    Orquesta la lógica de negocio para registro, login y validación.
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register_user(self, user_data: UserCreate) -> User:
        """
        Registra un nuevo usuario.
        Lanza excepción si el email ya existe.
        """
        # Verificar si el usuario ya existe
        existing_user = self.user_repository.find_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash de la contraseña
        password_hash = hash_password(user_data.password)

        # Crear usuario
        new_user = User(email=user_data.email, password_hash=password_hash)

        # Guardar en repositorio
        return self.user_repository.save(new_user)

    def login_user(self, credentials: UserLogin) -> Optional[str]:
        """
        Autentica un usuario y retorna un JWT token.
        Retorna None si las credenciales son inválidas.
        """
        # Buscar usuario por email
        user = self.user_repository.find_by_email(credentials.email)
        if not user:
            return None

        # Verificar contraseña
        if not verify_password(credentials.password, user.password_hash):
            return None

        # Verificar que el usuario esté activo
        if not user.is_active:
            return None

        # Generar JWT token
        token_data = {"sub": str(user.id), "email": user.email}
        token = create_access_token(token_data)

        return token

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por ID."""
        return self.user_repository.find_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por email."""
        return self.user_repository.find_by_email(email)

