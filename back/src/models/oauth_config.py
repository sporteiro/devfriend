from typing import Optional

from pydantic import BaseModel


class OAuthConfigBase(BaseModel):
    integration_id: int
    client_id: str
    client_secret: str
    redirect_uri: str
    provider: str

class OAuthConfigCreate(OAuthConfigBase):
    pass

class OAuthConfigUpdate(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    provider: Optional[str] = None

class OAuthConfig(OAuthConfigBase):
    id: int

    class Config:
        from_attributes = True