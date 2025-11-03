import tempfile
import os
from typing import List
import re

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.contracts.form_comparator_service import FormComparatorService
from application.dtos import ComparisonResultDTO, FoundReferenceDTO, NotFoundElementDTO
from domain.entities.CHTElement import CHTElement
from domain.contracts.xlsform_repository import XLSFormRepository

class FormComparatorServiceImpl(FormComparatorService):
    """
    Concrete implementation of the FormComparatorService.
    """
    def __init__(self, xlsform_repository: XLSFormRepository):
        self._xlsform_repo = xlsform_repository

    def compare_form_with_sql(self, xlsform_content: bytes, sql_content: bytes, country_code: str) -> ComparisonResultDTO:
        sql_path = None
        try:
            all_elements: List[CHTElement] = self._xlsform_repo.get_elements_from_file(xlsform_content)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".sql") as tmp_sql:
                tmp_sql.write(sql_content)
                sql_path = tmp_sql.name

            founds: List[FoundReferenceDTO] = []
            not_founds: List[NotFoundElementDTO] = []
            not_found_bm: List[NotFoundElementDTO] = []

            for element in all_elements:
                if element.json_path:
                    sql_refs = self._find_sql_references_in_file(element.json_path, sql_path)
                    
                    if sql_refs and sql_refs['count'] > 0:
                        founds.append(FoundReferenceDTO(
                            element_name=element.question_name,
                            json_path=element.json_path,
                            count=sql_refs['count'],
                            lines=sql_refs['lines']
                        ))
                    else:
                        # Apply country-specific logic for RCI
                        if country_code.upper() == 'RCI' and element.question_name.endswith('_bm'):
                            not_found_bm.append(NotFoundElementDTO(element_name=element.question_name, json_path=element.json_path))
                        else:
                            not_founds.append(NotFoundElementDTO(element_name=element.question_name, json_path=element.json_path))

            return ComparisonResultDTO(founds=founds, not_founds=not_founds, not_found_bm_elements=not_found_bm)

        finally:
            if sql_path and os.path.exists(sql_path):
                os.unlink(sql_path)

    def _find_sql_references_in_file(self, json_path: str, sql_file_path: str) -> dict | None:
        references = {'count': 0, 'lines': []}
        try:
            with open(sql_file_path, 'r') as f:
                for i, line in enumerate(f, 1):
                    matches = re.findall(re.escape(json_path), line)
                    if matches:
                        references['count'] += len(matches)
                        references['lines'].append(i)
        except FileNotFoundError:
            return None
        return references
