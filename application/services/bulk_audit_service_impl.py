import sys
import os
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.contracts.bulk_audit_service import BulkAuditService
from application.dtos import BulkAuditResultDTO, SingleFormComparisonResultDTO, NotFoundElementDTO, RepeatGroupAuditResultDTO
from domain.contracts.cht_app_repository import CHTAppRepository
from domain.contracts.code_repository import CodeRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.xlsform_repository import XLSFormRepository
from domain.contracts.logger import Logger
from application.utils import get_view_name, get_repeat_group_view_name

class BulkAuditServiceImpl(BulkAuditService):
    def __init__(
        self,
        cht_app_repo: CHTAppRepository,
        code_repo: CodeRepository,
        dw_repo: DataWarehouseRepository,
        xlsform_repo: XLSFormRepository,
        logger: Logger
    ):
        self._cht_app_repo = cht_app_repo
        self._code_repo = code_repo
        self._dw_repo = dw_repo
        self._xlsform_repo = xlsform_repo
        self._logger = logger

    def perform_audit(self, country_code: str) -> BulkAuditResultDTO:
        self._logger.log_info(f"Starting bulk audit for country: {country_code}")
        installed_forms = self._cht_app_repo.get_installed_xform_ids(country_code)
        
        compared_forms: List[SingleFormComparisonResultDTO] = []
        missing_xlsforms: List[str] = []
        invalid_xlsforms: List[str] = []
        missing_views: List[str] = []

        project_id = "musoitproducts"
        dataset_id = "cht_mali_prod" if country_code.upper() == "MALI" else "cht_rci_prod"

        for form_id in installed_forms:
            self._logger.log_info(f"Auditing form: {form_id}")
            
            try:
                xls_path_prefix = "muso-mali/forms/app/" if country_code.upper() == "MALI" else "muso-cdi/forms/app/"
                xls_path = f"{xls_path_prefix}{form_id}.xlsx"
                xls_content = self._code_repo.download_file(branch="master", file_path=xls_path)
            except FileNotFoundError:
                missing_xlsforms.append(form_id)
                continue
            except Exception as e:
                missing_xlsforms.append(f"{form_id} (Download Error)")
                continue

            try:
                main_body_elements = self._xlsform_repo.get_elements_from_file(xls_content)
                repeat_groups_data = self._xlsform_repo.get_repeat_groups_from_file(xls_content)
            except Exception as e:
                self._logger.log_exception(f"Could not parse XLSForm for '{form_id}'. It may be invalid. Error: {e}")
                invalid_xlsforms.append(form_id)
                continue

            not_found_main: List[NotFoundElementDTO] = []
            sql_content = None
            view_name = get_view_name(country_code, form_id)
            try:
                sql_content = self._dw_repo.get_view_query(project_id, dataset_id, view_name)
                for el in main_body_elements:
                    if el.json_path and el.json_path not in sql_content:
                        not_found_main.append(NotFoundElementDTO(element_name=el.question_name, json_path=el.json_path))
            except FileNotFoundError:
                missing_views.append(form_id)

            repeat_group_results: List[RepeatGroupAuditResultDTO] = []
            for repeat_name, repeat_data in repeat_groups_data.items():
                elements = repeat_data["elements"]
                json_path_in_parent = repeat_data["json_path_in_parent"]
                not_found_repeat: List[NotFoundElementDTO] = []
                handling_method = 'NOT_FOUND'
                
                if sql_content and f"UNNEST(JSON_EXTRACT_ARRAY(f.doc, '{json_path_in_parent}'))" in sql_content:
                    self._logger.log_info(f"Found ARRAY pattern for repeat group '{repeat_name}' in main view.")
                    handling_method = 'ARRAY_IN_MAIN_VIEW'
                    for el in elements:
                        if el.json_path and f"JSON_EXTRACT_SCALAR(item,'{el.json_path}')" not in sql_content:
                            not_found_repeat.append(NotFoundElementDTO(element_name=el.question_name, json_path=el.json_path))
                else:
                    repeat_view_name = get_repeat_group_view_name(form_id, repeat_name)
                    try:
                        repeat_sql_content = self._dw_repo.get_view_query(project_id, dataset_id, repeat_view_name)
                        handling_method = 'SEPARATE_VIEW'
                        for el in elements:
                            if el.json_path and el.json_path not in repeat_sql_content:
                                not_found_repeat.append(NotFoundElementDTO(element_name=el.question_name, json_path=el.json_path))
                    except FileNotFoundError:
                        self._logger.log_warning(f"Separate SQL view not found for repeat group: {repeat_name} in form: {form_id}")

                repeat_group_results.append(RepeatGroupAuditResultDTO(
                    repeat_group_name=repeat_name, handling_method=handling_method, elements=elements, not_found_elements=not_found_repeat
                ))

            if not_found_main or any(rg.not_found_elements or rg.handling_method == 'NOT_FOUND' for rg in repeat_group_results):
                compared_forms.append(SingleFormComparisonResultDTO(
                    form_id=form_id, 
                    not_found_elements=not_found_main,
                    repeat_groups=repeat_group_results
                ))

        return BulkAuditResultDTO(
            compared_forms=compared_forms, 
            missing_xlsforms=missing_xlsforms, 
            invalid_xlsforms=invalid_xlsforms,
            missing_views=missing_views
        )
