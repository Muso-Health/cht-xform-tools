
from __future__ import annotations

class CHTElement:
    def __init__(self, question_name: str, group: bool, odk_type: str, path: str, excel_line_number: int):
        self.question_name = question_name
        self.group = group
        self.odk_type = odk_type
        self.path = path
        self.excel_line_number = excel_line_number
        if self.group or self.question_name == 'nan' or self.odk_type == 'note':
            self.json_path = None
        else:
            self.json_path = self._calculate_json_path(path)

    def _calculate_json_path(self, odk_path: str) -> str | None:
        """
        Calculates the CHT JSON path based on the ODK path.
        """
        path_segments = odk_path.split('/')[2:] # Skips empty string and form_id
        
        if not path_segments:
            return None

        if path_segments[0] == 'inputs':
            return '$.' + '.'.join(path_segments)
        else:
            return '$.fields.' + '.'.join(path_segments)

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
