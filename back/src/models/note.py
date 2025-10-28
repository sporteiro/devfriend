from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Note(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    is_archived: bool = False

    class Config:
        from_attributes = True

    def update_content(self, new_content: str) -> None:
        self.content = new_content
