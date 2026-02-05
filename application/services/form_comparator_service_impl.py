import sys
import os
import re
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.contracts.form_comparator_service import FormComparatorService
from application.dtos import FullComparisonResultDTO, ComparisonResultDTO, FoundReferenceDTO, NotFoundElementDTO, RepeatGroupComparisonResultDTO, DbDocGroupComparisonResultDTO
from domain.contracts.xlsform_repository import XLSFormRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from application.utils import get_db_doc_group_view_name, get_repeat_group_view_name

class FormComparatorServiceImpl(FormComparatorService):
    """
    Concrete implementation of the FormComparatorService.
    """

    def __init__(self, xlsform_repository: XLSFormRepository, dw_repository: DataWarehouseRepository):
        self._xlsform_repo = xlsform_repository
        self._dw_repo = dw_repository

    def _is_extracted_in_struct(self, sql_content: str, json_path: str) -> bool:
        pattern = re.compile(r"JSON_EXTRACT_SCALAR\s*\(\s*item\s*,\s*['\"]" + re.escape(json_path) + r"['\"]\s*\)", re.IGNORECASE | re.DOTALL)
        return pattern.search(sql_content) is not None

    def compare_form_with_sql(self, xls_content: bytes, sql_content: bytes, country: str, form_id: str, project_id: str, dataset_id: str) -> FullComparisonResultDTO:
        """
        Compares all parts of an XLSForm with SQL content, automatically fetching related views.
        """
        parsed_data = self._xlsform_repo.get_elements_from_file(xls_content)
        main_elements = parsed_data.get("main_elements", [])
        repeat_groups_data = parsed_data.get("repeat_groups", [])
        db_doc_groups_data = parsed_data.get("db_doc_groups", [])
        
        sql_content_str = sql_content.decode('utf-8')

        # --- 1. Compare Main Body ---
        main_body_comparison = self._compare_elements_to_sql(main_elements, sql_content_str, country)

        # --- 2. Compare Repeat Groups ---
        repeat_comparisons = []
        for repeat_name, repeat_data in repeat_groups_data.items():
            elements, json_path_in_parent = repeat_data["elements"], repeat_data["json_path_in_parent"]
            handling_method = 'NOT_FOUND'
            comparison_result = ComparisonResultDTO()

            if f"UNNEST(JSON_EXTRACT_ARRAY(f.doc, '{json_path_in_parent}'))" in sql_content_str:
                handling_method = 'ARRAY_IN_MAIN_VIEW'
                founds, not_founds = [], []
                for el in elements:
                    if el.json_path and self._is_extracted_in_struct(sql_content_str, el.json_path):
                        founds.append(FoundReferenceDTO(el.question_name, el.json_path, 1, []))
                    elif el.json_path:
                        not_founds.append(NotFoundElementDTO(el.question_name, el.json_path))
                comparison_result = ComparisonResultDTO(founds=founds, not_founds=not_founds)
            else:
                view_name = get_repeat_group_view_name(form_id, repeat_name)
                try:
                    repeat_sql = self._dw_repo.get_view_query(project_id, dataset_id, view_name)
                    handling_method = 'SEPARATE_VIEW'
                    comparison_result = self._compare_elements_to_sql(elements, repeat_sql, country)
                except FileNotFoundError:
                    # All elements are considered not found
                    not_founds = [NotFoundElementDTO(el.question_name, el.json_path) for el in elements if el.json_path]
                    comparison_result = ComparisonResultDTO(not_founds=not_founds)

            repeat_comparisons.append(RepeatGroupComparisonResultDTO(repeat_name, handling_method, comparison_result))

        # --- 3. Compare DB-Doc Groups ---
        db_doc_comparisons = []
        for group_name, elements in db_doc_groups_data.items():
            view_name = get_db_doc_group_view_name(form_id, group_name)
            view_found = False
            comparison_result = ComparisonResultDTO()
            try:
                db_doc_sql = self._dw_repo.get_view_query(project_id, dataset_id, view_name)
                view_found = True
                comparison_result = self._compare_elements_to_sql(elements, db_doc_sql, country)
            except FileNotFoundError:
                not_founds = [NotFoundElementDTO(el.question_name, el.json_path) for el in elements if el.json_path]
                comparison_result = ComparisonResultDTO(not_founds=not_founds)

            db_doc_comparisons.append(DbDocGroupComparisonResultDTO(group_name, view_found, comparison_result))

        return FullComparisonResultDTO(main_body_comparison, repeat_comparisons, db_doc_comparisons)

    def _compare_elements_to_sql(self, elements: List, sql_content: str, country: str) -> ComparisonResultDTO:
        founds, not_founds, bm_not_founds = [], [], []
        for el in elements:
            if el.json_path:
                try:
                    matches = list(re.finditer(re.escape(el.json_path), sql_content))
                except re.error:
                    matches = []
                
                if matches:
                    lines = [sql_content[:match.start()].count('\n') + 1 for match in matches]
                    founds.append(FoundReferenceDTO(el.question_name, el.json_path, len(matches), lines))
                else:
                    if country == 'RCI' and el.question_name.endswith('_bm'):
                        bm_not_founds.append(NotFoundElementDTO(el.question_name, el.json_path))
                    else:
                        not_founds.append(NotFoundElementDTO(el.question_name, el.json_path))
        return ComparisonResultDTO(founds, not_founds, bm_not_founds)
