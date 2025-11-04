from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class Secret(BaseModel):
    id: Optional[int] = None
    user_id: int
    name: str
    encrypted_value: str  # Encrypted JSON (with all secret fields)
    service_type: str  # Example: 'github', 'gmail', etc.
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SecretCreate(BaseModel):
    name: str
    service_type: str
    # datos_secrets is a dictionary with all sensitive fields, will be converted to JSON and encrypted
    datos_secrets: Dict[str, Any]

class SecretResponse(BaseModel):
    id: int
    user_id: int
    name: str
    service_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    # encrypted_value is never exposed in API response
    class Config:
        from_attributes = True
