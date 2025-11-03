import pandas as pd
import tempfile
import os
from typing import List

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.xlsform_repository import XLSFormRepository
from domain.entities.CHTElement import CHTElement

class PandasXLSFormRepository(XLSFormRepository):
    """
    An implementation of the XLSFormRepository that uses the pandas library
    to read and parse the .xlsx file.
    """

    def get_elements_from_file(self, file_content: bytes) -> List[CHTElement]:
        """
        Parses the content of an XLSForm file using pandas.
        """
        # pandas requires a file path, so we write the bytes to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_file.write(file_content)
            temp_file_path = tmp_file.name

        try:
            try:
                settings_df = pd.read_excel(temp_file_path, sheet_name='settings')
                form_name = settings_df.iloc[0]['form_id']
            except (ValueError, KeyError, IndexError):
                form_name = 'my_form'

            survey_df = pd.read_excel(temp_file_path, sheet_name='survey')
            elements = []
            group_stack = []

            for index, row in survey_df.iterrows():
                excel_line_number = index + 2
                q_type = str(row.get('type', ''))
                q_name = str(row.get('name', ''))


                is_group = 'begin group' in q_type

                if 'begin group' in q_type:
                    path = f"/{form_name}/{'/'.join(group_stack)}/{q_name}" if group_stack else f"/{form_name}/{q_name}"
                    group_stack.append(q_name)
                elif 'end group' in q_type:
                    if group_stack:
                        group_stack.pop()
                    continue
                else:
                    path = f"/{form_name}/{'/'.join(group_stack)}/{q_name}" if group_stack else f"/{form_name}/{q_name}"

                elements.append(CHTElement(
                    question_name=q_name,
                    group=is_group,
                    odk_type=q_type,
                    path=path,
                    excel_line_number=excel_line_number
                ))

            return elements
        finally:
            # Ensure the temporary file is cleaned up
            os.unlink(temp_file_path)
