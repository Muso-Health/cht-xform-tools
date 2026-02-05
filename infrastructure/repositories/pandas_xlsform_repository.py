import pandas as pd
import tempfile
import os
from typing import List, Dict, Any

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.xlsform_repository import XLSFormRepository
from domain.entities.CHTElement import CHTElement

class PandasXLSFormRepository(XLSFormRepository):
    """
    An implementation of the XLSFormRepository that uses a robust state machine
    to parse the .xlsx file and correctly handle all nested contexts.
    """

    def get_elements_from_file(self, file_content: bytes) -> Dict[str, Any]:
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
            
            main_elements, repeats_data, db_docs_data = [], {}, {}
            group_stack = []
            active_repeat = None
            active_db_doc = None

            for index, row in survey_df.iterrows():
                excel_line_number = index + 2
                q_type = str(row.get('type', ''))
                q_name = str(row.get('name', ''))
                
                db_doc_val = str(row.get('instance::db-doc', 'false')).lower()
                is_db_doc = db_doc_val in ['true', '1', 'yes', '1.0']

                # --- STATE TRANSITIONS ---
                if 'begin group' in q_type:
                    group_name = q_name if q_name and q_name != 'nan' else f'unnamed_group_{excel_line_number}'
                    if active_db_doc:
                        active_db_doc['group_stack'].append(group_name)
                    elif active_repeat:
                        active_repeat['group_stack'].append(group_name)
                    else:
                        group_stack.append(group_name)
                    
                    if is_db_doc and not active_db_doc:
                        active_db_doc = {"name": group_name, "elements": [], "group_stack": []}
                    continue

                elif 'end group' in q_type:
                    if active_db_doc:
                        if active_db_doc['group_stack']:
                            active_db_doc['group_stack'].pop()
                        else:
                            db_docs_data[active_db_doc['name']] = active_db_doc['elements']
                            active_db_doc = None
                            group_stack.pop()
                    elif active_repeat:
                        if active_repeat['group_stack']:
                            active_repeat['group_stack'].pop()
                    elif group_stack:
                        group_stack.pop()
                    continue

                elif 'begin repeat' in q_type:
                    parent_json_path = '$.fields.' + '.'.join(group_stack + [q_name])
                    active_repeat = {"name": q_name, "elements": [], "group_stack": [], "json_path_in_parent": parent_json_path}
                    continue
                elif 'end repeat' in q_type:
                    if active_repeat:
                        repeats_data[active_repeat["name"]] = {"elements": active_repeat["elements"], "json_path_in_parent": active_repeat["json_path_in_parent"]}
                    active_repeat = None
                    continue

                # --- ELEMENT PROCESSING ---
                if pd.isna(row.get('name')) or not q_name or q_name == 'nan':
                    continue

                if active_db_doc:
                    path_parts = active_db_doc["group_stack"] + [q_name]
                    path = f"/{form_name}/{active_db_doc['name']}/{'/'.join(path_parts)}"
                    json_path = '$.' + '.'.join(path_parts) if q_type != 'note' else None
                    active_db_doc["elements"].append(CHTElement(q_name, False, q_type, path, excel_line_number, json_path))
                elif active_repeat:
                    path_parts = active_repeat["group_stack"] + [q_name]
                    path = f"/{active_repeat['name']}/{'/'.join(path_parts)}"
                    json_path = '$.' + '.'.join(path_parts) if q_type != 'note' else None
                    active_repeat["elements"].append(CHTElement(q_name, False, q_type, path, excel_line_number, json_path))
                else:
                    path_parts = group_stack + [q_name]
                    path = f"/{form_name}/{'/'.join(path_parts)}"
                    json_path = None
                    if q_type != 'note':
                        if group_stack and group_stack[0] == 'inputs':
                            json_path = '$.' + '.'.join(path_parts)
                        else:
                            json_path = '$.fields.' + '.'.join(path_parts)
                    main_elements.append(CHTElement(q_name, False, q_type, path, excel_line_number, json_path))

            return {"main_elements": main_elements, "repeat_groups": repeats_data, "db_doc_groups": db_docs_data}
        finally:
            os.unlink(temp_file_path)

    # Obsolete methods, kept only to satisfy the abstract class contract.
    def get_repeat_groups_from_file(self, file_content: bytes) -> Dict[str, Dict[str, Any]]: return {}
    def get_db_doc_groups_from_file(self, file_content: bytes) -> Dict[str, List[CHTElement]]: return {}
