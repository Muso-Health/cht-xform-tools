import pandas as pd
import tempfile
import os
from typing import List

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.rich_xlsform_repository import RichXLSFormRepository
from domain.entities.RichCHTElement import RichCHTElement

class PandasRichXLSFormRepository(RichXLSFormRepository):
    """
    An implementation of the RichXLSFormRepository that uses the pandas library
    to read and parse the .xlsx file into RichCHTElement objects.
    """

    def get_survey_sheet_as_markdown(self, file_content: bytes) -> str:
        """
        Reads the 'survey' sheet from an XLSForm file and returns it as a Markdown table.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_file.write(file_content)
            temp_file_path = tmp_file.name
        
        try:
            survey_df = pd.read_excel(temp_file_path, sheet_name='survey').fillna('')
            # To prevent huge prompts, we only select the most relevant columns for context.
            relevant_columns = [
                'type', 'name', 'label', 'label::fr', 'label::en', 'label::bm', 
                'calculation', 'required', 'relevant', 'constraint', 'choice_filter'
            ]
            # Filter the DataFrame to only include columns that actually exist in the sheet
            existing_relevant_columns = [col for col in relevant_columns if col in survey_df.columns]
            filtered_df = survey_df[existing_relevant_columns]
            
            return filtered_df.to_markdown(index=False)
        finally:
            os.unlink(temp_file_path)

    def get_rich_elements_from_file(self, file_content: bytes) -> List[RichCHTElement]:
        """
        Parses the content of an XLSForm file using pandas, including all title and calculation columns.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_file.write(file_content)
            temp_file_path = tmp_file.name

        try:
            try:
                settings_df = pd.read_excel(temp_file_path, sheet_name='settings')
                form_name = settings_df.iloc[0]['form_id']
            except (ValueError, KeyError, IndexError):
                form_name = 'my_form'

            survey_df = pd.read_excel(temp_file_path, sheet_name='survey').fillna('')
            elements = []
            group_stack = []

            for index, row in survey_df.iterrows():
                excel_line_number = index + 2
                q_type = str(row.get('type', ''))
                q_name = str(row.get('name', ''))



                # Capture titles and calculation
                titles = {
                    'fr': str(row.get('label::fr', '')),
                    'en': str(row.get('label::en', '')),
                    'bm': str(row.get('label::bm', ''))
                }
                calculation = str(row.get('calculation', ''))

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

                elements.append(RichCHTElement(
                    question_name=q_name,
                    group=is_group,
                    odk_type=q_type,
                    path=path,
                    excel_line_number=excel_line_number,
                    titles=titles,
                    calculation=calculation if calculation else None
                ))

            return elements
        finally:
            os.unlink(temp_file_path)
