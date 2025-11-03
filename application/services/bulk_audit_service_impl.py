import sys
import os
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.contracts.bulk_audit_service import BulkAuditService
from application.dtos import BulkAuditResultDTO, SingleFormComparisonResultDTO, NotFoundElementDTO
from domain.contracts.cht_app_repository import CHTAppRepository
from domain.contracts.code_repository import CodeRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.xlsform_repository import XLSFormRepository
from domain.contracts.logger import Logger

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
        self._view_name_exceptions = {
            "MALI": {
                "patient_assessment": "formview_assessment",
                "patient_assessment_over_5": "formview_assessment_over_5",
                "referral_followup_under_5": "formview_referral_followup_under5",
                "treatment_followup": "formview_treatment_follow_up",
                "prenatal_followup": "formview_prenatal",
                "behavior_change": "formview_behaviour_change"
            },
            "RCI": {
                "patient_assessment": "formview_assessment",
                "patient_assessment_over_5": "formview_assessment_over_5",
                "referral_followup_under_5": "formview_referral_followup_under5",
                "treatment_followup": "formview_treatment_followup",
                "prenatal_followup": "formview_prenatal"
            }
        }

    def _get_view_name(self, country_code: str, form_id: str) -> str:
        country_exceptions = self._view_name_exceptions.get(country_code.upper(), {})
        return country_exceptions.get(form_id, f"formview_{form_id}")

    def perform_audit(self, country_code: str) -> BulkAuditResultDTO:
        self._logger.log_info(f"Starting bulk audit for country: {country_code}")
        installed_forms = self._cht_app_repo.get_installed_xform_ids(country_code)
        
        compared_forms: List[SingleFormComparisonResultDTO] = []
        missing_xlsforms: List[str] = []
        missing_views: List[str] = []

        for form_id in installed_forms:
            try:
                self._logger.log_info(f"Auditing form: {form_id}")
                xls_path_prefix = "muso-mali/forms/app/" if country_code.upper() == "MALI" else "muso-cdi/forms/app/"
                xls_path = f"{xls_path_prefix}{form_id}.xlsx"
                xls_content = self._code_repo.download_file(branch="master", file_path=xls_path)

                view_name = self._get_view_name(country_code, form_id)
                project_id = "musoitproducts"
                dataset_id = "cht_mali_prod" if country_code.upper() == "MALI" else "cht_rci_prod"
                
                try:
                    sql_content = self._dw_repo.get_view_query(project_id, dataset_id, view_name)
                    elements = self._xlsform_repo.get_elements_from_file(xls_content)
                    not_found_elements: List[NotFoundElementDTO] = []
                    for el in elements:
                        if el.json_path and el.json_path not in sql_content:
                            not_found_elements.append(NotFoundElementDTO(element_name=el.question_name, json_path=el.json_path))
                    
                    if not_found_elements:
                        self._logger.log_warning(f"Found {len(not_found_elements)} discrepancies in form: {form_id}")
                        compared_forms.append(SingleFormComparisonResultDTO(form_id=form_id, not_found_elements=not_found_elements))

                except FileNotFoundError:
                    self._logger.log_warning(f"BigQuery view not found for form: {form_id}")
                    missing_views.append(form_id)

            except FileNotFoundError:
                self._logger.log_warning(f"XLSForm not found in GitHub for form: {form_id}")
                missing_xlsforms.append(form_id)
            except Exception as e:
                self._logger.log_exception(f"Could not process form '{form_id}'. Reason: {e}")
                missing_xlsforms.append(f"{form_id} (Processing Error)")

        self._logger.log_info("Bulk audit finished.")
        return BulkAuditResultDTO(compared_forms=compared_forms, missing_xlsforms=missing_xlsforms, missing_views=missing_views)
