from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class CHTElement:
    """
    Represents a single element (question, group, note, etc.) within an XLSForm.
    This is a simple data container; path calculation is handled by the repository.
    """
    question_name: str
    group: bool
    odk_type: str
    path: str
    excel_line_number: int
    json_path: str | None  # The JSON path, or None if not applicable (e.g., for groups)

    def __repr__(self) -> str:
        return f"CHTElement(name='{self.question_name}', path='{self.path}', json_path='{self.json_path}', line={self.excel_line_number})"

    def belongs_to(self, other_element: CHTElement) -> bool:
        """
        Checks if this element belongs to another element (i.e., is a descendant in the path).
        """
        if not other_element.group:
            return False
        return self.path.startswith(other_element.path + '/')

    def __lt__(self, other: CHTElement) -> bool:
        """
        Allows using the '<' operator to check for belonging.
        """
        return self.belongs_to(other)

    def form_id(self):
        return self.path.split('/')[1]
