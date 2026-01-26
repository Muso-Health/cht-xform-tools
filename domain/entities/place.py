from __future__ import annotations
from typing import Optional
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from entities.cht_contact import CHTContact

class Place(CHTContact):
    """
    Represents a geographical or organizational place in the CHT hierarchy.
    """
    def __init__(self, place_type: str, parent: Optional[Place] = None):
        # Basic validation of the hierarchy
        if place_type == 'c10_site' and parent is not None:
            raise ValueError("A c10_site cannot have a parent.")
        if place_type == 'c50_family' and (parent is None or parent.contact_type != 'c40_chw_area'):
            raise ValueError("A c50_family must have a c40_chw_area as a parent.")
        
        super().__init__(contact_type=place_type, parent=parent)

    def get_description(self) -> str:
        """Returns a human-readable description of the place."""
        descriptions = {
            'c10_site': "the site",
            'c20_health_area': "the health area",
            'c30_supervisor_area': "the supervisor's area",
            'c40_chw_area': "the CHW's area",
            'c50_family': "the family"
        }
        return descriptions.get(self.contact_type, "an unknown place")
