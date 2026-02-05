import pandas as pd
import tempfile
import os
from typing import List, Dict, Any
from collections import defaultdict

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.xlsform_repository import XLSFormRepository
from domain.entities.CHTElement import CHTElement

class PandasXLSFormRepository(XLSFormRepository):
    """
    An implementation of the XLSFormRepository that uses the pandas library
    to read and parse the .xlsx file. This repository is responsible for
    correctly constructing both the ODK path and the CHT JSONPath.
    """

    def get_repeat_groups_from_file(self, file_content: bytes) -> Dict[str, Dict[str, Any]]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_file.write(file_content)
            temp_file_path = tmp_file.name

        try:
            survey_df = pd.read_excel(temp_file_path, sheet_name='survey').fillna('')
            # This will hold the final, structured data for all repeats
            repeats_data = {}
            
            # State trackers
            group_stack = []
            current_repeat = None
            in_repeat_group = False

            for index, row in survey_df.iterrows():
                excel_line_number = index + 2
                q_type = str(row.get('type', ''))
                q_name = str(row.get('name', ''))

                # Handle state transitions first
                if 'begin repeat' in q_type:
                    in_repeat_group = True
                    # This is the crucial part: capture the main body's group stack
                    # at the moment the repeat begins.
                    parent_json_path = '$.fields.' + '.'.join(group_stack + [q_name])
                    current_repeat = {
                        "name": q_name,
                        "elements": [],
                        "group_stack": [],
                        "json_path_in_parent": parent_json_path
                    }
                    continue
                elif 'end repeat' in q_type:
                    if current_repeat:
                        repeats_data[current_repeat["name"]] = {
                            "elements": current_repeat["elements"],
                            "json_path_in_parent": current_repeat["json_path_in_parent"]
                        }
                    in_repeat_group = False
                    current_repeat = None
                    continue

                # Now, process the row based on the current state
                if in_repeat_group and current_repeat:
                    if 'begin group' in q_type:
                        current_repeat["group_stack"].append(q_name)
                    elif 'end group' in q_type:
                        if current_repeat["group_stack"]:
                            current_repeat["group_stack"].pop()
                    else:
                        if pd.isna(row.get('name')) or not q_name or q_name == 'nan':
                            continue
                        
                        path_parts = current_repeat["group_stack"] + [q_name]
                        path = f"/{current_repeat['name']}/{'/'.join(path_parts)}"
                        json_path = '$.' + '.'.join(path_parts) if q_type != 'note' else None

                        current_repeat["elements"].append(CHTElement(
                            question_name=q_name, group=False, odk_type=q_type, path=path,
                            excel_line_number=excel_line_number, json_path=json_path
                        ))
                else: # We are in the main body of the form
                    if 'begin group' in q_type:
                        group_stack.append(q_name)
                    elif 'end group' in q_type:
                        if group_stack:
                            group_stack.pop()
            
            return repeats_data
        finally:
            os.unlink(temp_file_path)

    def get_elements_from_file(self, file_content: bytes) -> List[CHTElement]:
        # This function remains largely the same as the last correct version
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
            in_repeat_group = False

            for index, row in survey_df.iterrows():
                excel_line_number = index + 2
                q_type = str(row.get('type', ''))
                q_name = str(row.get('name', ''))

                if 'begin repeat' in q_type:
                    in_repeat_group = True
                    continue
                elif 'end repeat' in q_type:
                    in_repeat_group = False
                    continue
                
                if in_repeat_group:
                    continue

                if 'begin group' in q_type:
                    group_name = q_name if q_name and q_name != 'nan' else f'unnamed_group_{excel_line_number}'
                    group_stack.append(group_name)
                    continue
                elif 'end group' in q_type:
                    if group_stack:
                        group_stack.pop()
                    continue
                
                if pd.isna(row.get('name')) or not q_name or q_name == 'nan':
                    continue
                
                path_prefix = f"/{form_name}"
                current_path_parts = group_stack + [q_name]
                full_path = f"{path_prefix}/{'/'.join(current_path_parts)}"
                
                json_path = None
                if q_type != 'note':
                    if group_stack and group_stack[0] == 'inputs':
                         json_path_parts = group_stack + [q_name]
                         json_path = '$.' + '.'.join(json_path_parts)
                    else:
                        json_path_parts = ['fields'] + group_stack + [q_name]
                        json_path = '$.' + '.'.join(json_path_parts)

                elements.append(CHTElement(
                    question_name=q_name, group=False, odk_type=q_type, path=full_path,
                    excel_line_number=excel_line_number, json_path=json_path
                ))
            return elements
        finally:
            os.unlink(temp_file_path)
