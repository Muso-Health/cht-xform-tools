from __future__ import annotations
from typing import Dict, Optional

class RichCHTElement:
    """
    A rich representation of an XLSForm element, including multilingual titles and calculations.
    This entity is used for comparing two XLSForms and is isolated from the original CHTElement.
    """
    def __init__(
        self, 
        question_name: str, 
        group: bool, 
        odk_type: str, 
        path: str, 
        excel_line_number: int,
        titles: Optional[Dict[str, str]] = None,
        calculation: Optional[str] = None
    ):
        self.question_name = question_name
        self.group = group
        self.odk_type = odk_type
        self.path = path
        self.excel_line_number = excel_line_number
        self.titles = titles if titles is not None else {}
        self.calculation = calculation

        if self.group or self.question_name == 'nan' or self.odk_type == 'note':
            self.json_path = None
        else:
            self.json_path = self._calculate_json_path(path)

    def _calculate_json_path(self, odk_path: str) -> str | None:
        path_segments = odk_path.split('/')[2:]
        if not path_segments:
            return None
        if path_segments[0] == 'inputs':
            return '$.' + '.'.join(path_segments)
        else:
            return '$.fields.' + '.'.join(path_segments)

    def __repr__(self) -> str:
        return f"RichCHTElement(name='{self.question_name}', path='{self.path}')"
