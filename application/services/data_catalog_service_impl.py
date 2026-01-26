import sys
import os
from typing import List

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.contracts.data_catalog_service import DataCatalogService
from application.dtos import DataCatalogResultDTO, DataCatalogRowDTO
from domain.contracts.cht_app_repository import CHTAppRepository
from domain.contracts.code_repository import CodeRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.rich_xlsform_repository import RichXLSFormRepository
from domain.contracts.sql_parser_repository import SQLParserRepository
from domain.contracts.logger import Logger

class DataCatalogServiceImpl(DataCatalogService):
    """
    Concrete implementation of the DataCatalogService.
    """

    def __init__(
        self,
        cht_app_repo: CHTAppRepository,
        code_repo: CodeRepository,
        dw_repo: DataWarehouseRepository,
        xlsform_repo: RichXLSFormRepository,
        sql_parser_repo: SQLParserRepository,
        logger: Logger
    ):
        self._cht_app_repo = cht_app_repo
        self._code_repo = code_repo
        self._dw_repo = dw_repo
        self._xlsform_repo = xlsform_repo
        self._sql_parser_repo = sql_parser_repo
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

    def generate_catalog(self, country_code: str) -> DataCatalogResultDTO:
        self._logger.log_info(f"Starting data catalog generation for country: {country_code}")
        installed_forms = self._cht_app_repo.get_installed_xform_ids(country_code)
        
        all_catalog_rows: List[DataCatalogRowDTO] = []

        for form_id in installed_forms:
            try:
                self._logger.log_info(f"Processing form: {form_id}")

                # 1. Fetch XLSForm from GitHub
                xls_path_prefix = "muso-mali/forms/app/" if country_code.upper() == "MALI" else "muso-cdi/forms/app/"
                xls_path = f"{xls_path_prefix}{form_id}.xlsx"
                xls_content = self._code_repo.download_file(branch="master", file_path=xls_path)
                
                # 2. Fetch BigQuery View SQL
                view_name = self._get_view_name(country_code, form_id)
                project_id = "musoitproducts"
                dataset_id = "cht_mali_prod" if country_code.upper() == "MALI" else "cht_rci_prod"
                sql_content = self._dw_repo.get_view_query(project_id, dataset_id, view_name)

                # 3. Parse both artifacts
                xls_elements = self._xlsform_repo.get_rich_elements_from_file(xls_content)
                xls_elements_map = {el.json_path: el for el in xls_elements if el.json_path}
                
                sql_columns = self._sql_parser_repo.parse_columns(sql_content)

                # 4. Correlate and generate rows
                for col in sql_columns:
                    if col.json_path in xls_elements_map:
                        element = xls_elements_map[col.json_path]
                        row = DataCatalogRowDTO(
                            formview_name=view_name,
                            xlsform_name=form_id,
                            column_name=col.column_name,
                            sql_type=col.sql_type,
                            json_path=col.json_path,
                            odk_type=element.odk_type,
                            calculation=element.calculation or "", # Populate the new field
                            label_fr=element.titles.get('fr', ''),
                            label_en=element.titles.get('en', ''),
                            label_bm=element.titles.get('bm', '')
                        )
                        all_catalog_rows.append(row)
                    else:
                        self._logger.log_warning(f"Could not find matching XLSForm element for column '{col.column_name}' with path '{col.json_path}' in form '{form_id}'")

            except FileNotFoundError as e:
                self._logger.log_warning(f"Skipping form '{form_id}': Artifact not found. Reason: {e}")
            except Exception as e:
                self._logger.log_exception(f"An unexpected error occurred while processing form '{form_id}': {e}")

        self._logger.log_info(f"Data catalog generation finished. Found {len(all_catalog_rows)} entries.")
        return DataCatalogResultDTO(catalog_rows=all_catalog_rows)
