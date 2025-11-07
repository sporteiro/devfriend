import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status

from src.middleware.auth_middleware import get_current_user_id
from src.models.user import UserCreate, UserLogin, UserResponse
from src.repositories.postgresql_user_repository import PostgreSQLUserRepository
from src.services.auth_service import AuthService


# Load environment variables
load_dotenv()

router = APIRouter()

# PostgreSQL configuration from environment variables
db_config = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "devfriend"),
    "user": os.getenv("DB_USER", "devfriend"),
    "password": os.getenv("DB_PASSWORD", "devfriend"),
}

# Initialize service
auth_service = AuthService(PostgreSQLUserRepository(**db_config))


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    """
    try:
        user = auth_service.register_user(user_data)
        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/auth/login")
async def login(credentials: UserLogin):
    """
    Authenticate a user and return a JWT token.
    """
    token = auth_service.login_user(credentials)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user(user_id: int = Depends(get_current_user_id)):
    """
    Get the authenticated user's information.
    """
    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        is_active=user.is_active,
    )

