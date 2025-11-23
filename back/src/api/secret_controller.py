import os
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status

from src.middleware.auth_middleware import get_current_user_id
from src.models.secret import SecretCreate, SecretResponse
from src.repositories.postgresql_secret_repository import PostgreSQLSecretRepository
from src.services.secret_service import SecretService
from src.utils.get_db_config import GetDBConfig


load_dotenv()

router = APIRouter()
db_config = GetDBConfig().get_db_config()

secret_service = SecretService(PostgreSQLSecretRepository(**db_config))

@router.get("/secrets", response_model=List[SecretResponse])
async def list_secrets(user_id: int = Depends(get_current_user_id)):
    """List all credentials/secrets for the authenticated user."""
    return secret_service.list_secrets(user_id)

@router.post("/secrets", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def create_secret(data: SecretCreate, user_id: int = Depends(get_current_user_id)):
    """Create a new credential/secret for the authenticated user."""
    return secret_service.create_secret(user_id, data)

@router.get("/secrets/get-decryptable")
async def get_decryptable_decrypted_secrets(user_id: int = Depends(get_current_user_id)):
    repo = PostgreSQLSecretRepository()
    secrets = repo.find_all_by_type_decrypted(user_id, "custom")
    return secrets

@router.get("/secrets/{secret_id}", response_model=SecretResponse)
async def get_secret(secret_id: int, user_id: int = Depends(get_current_user_id)):
    """Get details (metadata only, never the secret in plain text)."""
    secret = secret_service.get_secret(user_id, secret_id)
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found or unauthorized")
    return SecretResponse(**secret.dict())

@router.put("/secrets/{secret_id}", response_model=SecretResponse)
async def update_secret(secret_id: int, data: dict, user_id: int = Depends(get_current_user_id)):
    """Update secret data for the user."""
    secret = secret_service.update_secret(user_id, secret_id, data)
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found or unauthorized")
    return secret

@router.delete("/secrets/{secret_id}")
async def delete_secret(secret_id: int, user_id: int = Depends(get_current_user_id)):
    ok = secret_service.delete_secret(user_id, secret_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Secret not found or unauthorized")
    return {"message": "Secret deleted successfully"}
