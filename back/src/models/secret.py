from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class Secret(BaseModel):
    id: Optional[int] = None
    user_id: int
    name: str
    encrypted_value: str  # JSON cifrado (con todos los campos secretos)
    service_type: str  # Ej: 'github', 'gmail', etc.
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SecretCreate(BaseModel):
    name: str
    service_type: str
    # datos_secrets es un diccionario con todos los campos sensibles, se convertirá a JSON y será cifrado
    datos_secrets: Dict[str, Any]

class SecretResponse(BaseModel):
    id: int
    user_id: int
    name: str
    service_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    # No se expone encrypted_value nunca en respuesta API
    class Config:
        from_attributes = True
