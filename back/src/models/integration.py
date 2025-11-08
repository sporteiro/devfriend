from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class IntegrationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    secret_id: Optional[int] = None
    service_type: str
    config: Optional[Dict[str, Any]] = None
    is_active: bool = True

class IntegrationCreate(IntegrationBase):
    pass

class IntegrationUpdate(BaseModel):
    secret_id: Optional[int] = None
    service_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class Integration(IntegrationBase):
    id: int
    created_at: datetime
    updated_at: datetime
