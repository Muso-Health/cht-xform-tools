from __future__ import annotations
from typing import Optional
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from domain.entities.cht_contact import CHTContact
from domain.entities.place import Place

class Person(CHTContact):
    """
    Represents a person in the CHT hierarchy, associated with a specific role and place.
    """
    def __init__(self, role: str, parent: Place):
        self.role = role
        super().__init__(contact_type='person', parent=parent)

    def get_description(self) -> str:
        """Returns a human-readable description of the person's role."""
        descriptions = {
            'Patient': "the patient",
            'CHW': "the Community Health Worker (CHW)",
            'Supervisor': "the Supervisor"
        }
        return descriptions.get(self.role, "a person")
