from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Note(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    created_at: Optional[datetime] = None
    
    def update_content(self, new_content: str) -> None:
        self.content = new_content
