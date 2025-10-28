from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Note(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    created_at: Optional[datetime] = None

    def update_content(self, new_content: str) -> None:
        self.content = new_content
