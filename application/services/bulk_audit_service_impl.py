import sys
import os
import re
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.contracts.bulk_audit_service import BulkAuditService
from application.dtos import BulkAuditResultDTO, SingleFormComparisonResultDTO, NotFoundElementDTO, RepeatGroupAuditResultDTO, DbDocGroupAuditResultDTO
from domain.contracts.cht_app_repository import CHTAppRepository
from domain.contracts.code_repository import CodeRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.xlsform_repository import XLSFormRepository
from domain.contracts.logger import Logger
from application.utils import get_view_name, get_repeat_group_view_name, get_db_doc_group_view_name

class BulkAuditServiceImpl(BulkAuditService):
    def __init__(self, cht_app_repo: CHTAppRepository, code_repo: CodeRepository, dw_repo: DataWarehouseRepository, xlsform_repo: XLSFormRepository, logger: Logger):
        self._cht_app_repo = cht_app_repo
        self._code_repo = code_repo
        self._dw_repo = dw_repo
        self._xlsform_repo = xlsform_repo
        self._logger = logger

    def _is_extracted_in_struct(self, sql_content: str, json_path: str) -> bool:
        pattern = re.compile(
            r"JSON_EXTRACT_SCALAR\s*\(\s*item\s*,\s*['\"]" + re.escape(json_path) + r"['\"]\s*\)",
            re.IGNORECASE | re.DOTALL
        )
        return pattern.search(sql_content) is not None

    def _is_unnest_pattern_present(self, sql_content: str, repeat_group_json_path: str) -> bool:
        """
        Robustly checks for the UNNEST(JSON_EXTRACT_ARRAY(...)) pattern using regex,
        ignoring whitespace, newlines, and the specific table alias (e.g., f.doc).
        """
        pattern = re.compile(
            r"UNNEST\s*\(\s*JSON_EXTRACT_ARRAY\s*\([^,]+,\s*['\"]" + re.escape(repeat_group_json_path) + r"['\"]\s*\)",
            re.IGNORECASE | re.DOTALL
        )
        return pattern.search(sql_content) is not None

    def perform_audit(self, country_code: str) -> BulkAuditResultDTO:
        self._logger.log_info(f"Starting bulk audit for country: {country_code}")
        installed_forms = self._cht_app_repo.get_installed_xform_ids(country_code)
        
        compared_forms, missing_xlsforms, invalid_xlsforms, missing_views = [], [], [], []
        project_id = "musoitproducts"
        dataset_id = "cht_mali_prod" if country_code.upper() == "MALI" else "cht_rci_prod"

        for form_id in installed_forms:
            self._logger.log_info(f"Auditing form: {form_id}")
            
            try:
                xls_path = f"muso-mali/forms/app/{form_id}.xlsx" if country_code.upper() == "MALI" else f"muso-cdi/forms/app/{form_id}.xlsx"
                xls_content = self._code_repo.download_file(branch="master", file_path=xls_path)
            except FileNotFoundError:
                missing_xlsforms.append(form_id); continue
            except Exception:
                missing_xlsforms.append(f"{form_id} (Download Error)"); continue

            try:
                parsed_data = self._xlsform_repo.get_elements_from_file(xls_content)
                main_elements, repeat_groups_data, db_doc_groups_data = parsed_data["main_elements"], parsed_data["repeat_groups"], parsed_data["db_doc_groups"]
            except Exception as e:
                self._logger.log_exception(f"Could not parse XLSForm for '{form_id}'. Error: {e}"); invalid_xlsforms.append(form_id); continue

            not_found_main, sql_content = [], None
            view_name = get_view_name(country_code, form_id)
            try:
                sql_content = self._dw_repo.get_view_query(project_id, dataset_id, view_name)
                for el in main_elements:
                    if el.json_path and el.json_path not in sql_content:
                        not_found_main.append(NotFoundElementDTO(el.question_name, el.json_path))
            except FileNotFoundError:
                missing_views.append(form_id)

            repeat_group_results = self._audit_repeat_groups(form_id, repeat_groups_data, sql_content, project_id, dataset_id)
            db_doc_group_results = self._audit_db_doc_groups(form_id, db_doc_groups_data, project_id, dataset_id)

            if not_found_main or repeat_group_results or db_doc_group_results:
                compared_forms.append(SingleFormComparisonResultDTO(form_id, not_found_main, repeat_group_results, db_doc_group_results))

        return BulkAuditResultDTO(compared_forms, missing_xlsforms, invalid_xlsforms, missing_views)

    def _audit_repeat_groups(self, form_id, repeat_groups_data, main_sql_content, project_id, dataset_id):
        results = []
        for repeat_name, repeat_data in repeat_groups_data.items():
            elements, json_path_in_parent = repeat_data["elements"], repeat_data["json_path_in_parent"]
            not_found, handling_method = [], 'NOT_FOUND'
            
            if main_sql_content and self._is_unnest_pattern_present(main_sql_content, json_path_in_parent):
                handling_method = 'ARRAY_IN_MAIN_VIEW'
                for el in elements:
                    if el.json_path and not self._is_extracted_in_struct(main_sql_content, el.json_path):
                        not_found.append(NotFoundElementDTO(el.question_name, el.json_path))
            else:
                view_name = get_repeat_group_view_name(form_id, repeat_name)
                try:
                    sql = self._dw_repo.get_view_query(project_id, dataset_id, view_name)
                    handling_method = 'SEPARATE_VIEW'
                    for el in elements:
                        if el.json_path and el.json_path not in sql:
                            not_found.append(NotFoundElementDTO(el.question_name, el.json_path))
                except FileNotFoundError:
                    self._logger.log_warning(f"Separate view not found for repeat group: {repeat_name}")
            
            results.append(RepeatGroupAuditResultDTO(repeat_name, handling_method, elements, not_found))
        return results

    def _audit_db_doc_groups(self, form_id, db_doc_groups_data, project_id, dataset_id):
        results = []
        for group_name, elements in db_doc_groups_data.items():
            not_found, view_found = [], False
            view_name = get_db_doc_group_view_name(form_id, group_name)
            try:
                sql = self._dw_repo.get_view_query(project_id, dataset_id, view_name)
                view_found = True
                for el in elements:
                    if el.json_path and el.json_path not in sql:
                        not_found.append(NotFoundElementDTO(el.question_name, el.json_path))
            except FileNotFoundError:
                self._logger.log_warning(f"View not found for db-doc group: {group_name}")
            
            results.append(DbDocGroupAuditResultDTO(group_name, view_found, elements, not_found))
        return results
