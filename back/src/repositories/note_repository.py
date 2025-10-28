from abc import ABC, abstractmethod
from typing import List, Optional

from src.models.note import Note


class NoteRepository(ABC):
    @abstractmethod
    def save(self, note: Note) -> Note:
        pass

    @abstractmethod
    def find_all(self) -> List[Note]:
        pass

    @abstractmethod
    def find_by_id(self, note_id: int) -> Optional[Note]:
        pass

    @abstractmethod
    def find_by_user(self, user_id: int) -> List[Note]:
        pass

    @abstractmethod
    def delete(self, note_id: int) -> bool:
        pass
