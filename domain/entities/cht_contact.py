from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

class CHTContact(ABC):
    """
    Abstract base class representing a contact in the CHT hierarchy (either a Person or a Place).
    """
    def __init__(self, contact_type: str, parent: Optional[CHTContact] = None):
        self.contact_type = contact_type
        self.parent = parent

    @abstractmethod
    def get_description(self) -> str:
        """Returns a human-readable description of the contact."""
        pass
