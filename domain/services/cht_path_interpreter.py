from typing import Dict, List
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from entities.cht_contact import CHTContact
from entities.person import Person
from entities.place import Place

class CHTPathInterpreter:
    """
    A domain service that interprets CHT-specific path expressions
    and translates them into human-readable descriptions.
    """
    def __init__(self, form_context: Dict):
        self.form_context = form_context
        self.subject = None

    @staticmethod
    def lineage(contact_type: str) -> List[str]:
        if contact_type == 'patient':
            return  ['c50_family', 'c40_chw_area', 'c30_supervisor_area', 'c20_health_area', 'c10_site']
        elif contact_type == 'chw' or contact_type == 'c50_family':
            return ['c40_chw_area', 'c30_supervisor_area', 'c20_health_area', 'c10_site']
        elif contact_type == 'chw_supervisor' or contact_type == 'c40_chw_area':
            return ['c30_supervisor_area', 'c20_health_area', 'c10_site']
        elif contact_type == 'stock_manager' or contact_type == 'tb_focal_point' or contact_type == 'c30_supervisor_area':
            return ['c20_health_area', 'c10_site']
        elif contact_type == 'chw_manager' or contact_type == 'c20_health_area':
            return ['c10_site']
        else:
            return []


    def _build_initial_contact(self) -> CHTContact:
        """Builds the initial contact hierarchy based on the form context."""
        contact_type = self.form_context.get('contact_type', [])
        
        if not contact_type:
            raise ValueError("Form context is missing 'contact_type'.")

        if contact_type == ['person']:
            # Handle the case where the subject is a person
            self.subject = 'person'
            contact_role = self.form_context.get('contact_role', [None])[0]
            if contact_role:
                parent_hierarchy = CHTPathInterpreter.lineage(contact_role)
            else:
                parent_hierarchy = []

            parent = None
            for place_type in reversed(parent_hierarchy):
                parent = Place(place_type=place_type, parent=parent)

            return Person(role=contact_role, parent=parent)
        else:
            self.subject = contact_type
            # Handle the case where the subject is a place
            parent = None
            for place_type in reversed(contact_type):
                parent = Place(place_type=place_type, parent=parent)
            return parent


    def interpret_path(self, path: str) -> str:
        """
        Parses a CHT path expression and returns a human-readable description.
        Example: '../inputs/contact/parent/parent/contact' -> "The CHW for the patient's family's health area."
        """
        if not path.startswith('../inputs/') and not path.startswith('../../inputs/'):
            return "A standard calculated field."

        if path.startswith('../inputs/'):
            starter = '../inputs'
            path_segments = path.replace('../inputs/', '').split('/')
        else:
            starter = '../../inputs'
            path_segments = path.replace('../../inputs/', '').split('/')

        if len(path_segments)<1:
            return "A standard calculated field."

        return f" .In this case the {starter}/contact refers to a {self.subject}. The formula {path} refers to which property of which CHT contact?"

        current_contact = self._build_initial_contact()
        
        for segment in path_segments:
            if segment == 'contact':
                # This segment is handled by the initial context, so we just continue
                continue
            elif segment == 'parent':
                if current_contact.parent:
                    current_contact = current_contact.parent
                else:
                    return f"Error: Tried to access parent of a contact with no parent ({current_contact.get_description()})."
            else:
                # This handles specific fields on a contact, e.g., 'name', 'date_of_birth'
                # For now, we just describe the final contact.
                pass
        
        # After walking the path, describe the final contact
        final_description = self._get_final_description(current_contact)
        
        # Make the description relative to the original subject
        original_subject_context = self._build_initial_contact()
        original_subject = original_subject_context.get_description()
        
        return f"Refers to {final_description} related to {original_subject}."

    def _get_final_description(self, contact: CHTContact) -> str:
        """Generates a descriptive string for the final contact in the path."""
        if isinstance(contact, Person):
            # If the final contact is a person, describe their role and their parent place
            parent_desc = contact.parent.get_description() if contact.parent else "an unknown area"
            return f"{contact.get_description()} of {parent_desc}"
        elif isinstance(contact, Place):
            return contact.get_description()
        return "an unknown entity"
