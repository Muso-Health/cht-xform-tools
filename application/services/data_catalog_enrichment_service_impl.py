import sys
import os
from typing import Callable
from dependency_injector.providers import Configuration
from collections import defaultdict

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.contracts.data_catalog_enrichment_service import DataCatalogEnrichmentService
from application.dtos import DataCatalogResultDTO
from domain.contracts.semantic_comparator_repository import SemanticComparatorRepository
from domain.contracts.code_repository import CodeRepository
from domain.contracts.rich_xlsform_repository import RichXLSFormRepository
from domain.contracts.logger import Logger
from domain.services.cht_path_interpreter import CHTPathInterpreter

class DataCatalogEnrichmentServiceImpl(DataCatalogEnrichmentService):
    """
    Concrete implementation of the DataCatalogEnrichmentService.
    """

    def __init__(
        self, 
        semantic_repo: SemanticComparatorRepository, 
        code_repo: CodeRepository,
        xlsform_repo: RichXLSFormRepository,
        path_interpreter_factory: Callable[..., CHTPathInterpreter],
        form_context_config: Configuration,
        logger: Logger
    ):
        self._semantic_repo = semantic_repo
        self._code_repo = code_repo
        self._xlsform_repo = xlsform_repo
        self._path_interpreter_factory = path_interpreter_factory
        self._form_context_config = form_context_config
        self._logger = logger

    def enrich_catalog(
        self, 
        catalog: DataCatalogResultDTO, 
        country_code: str,
        mode: str, 
        form_filter: str
    ) -> DataCatalogResultDTO:
        
        self._logger.log_info(f"Starting data catalog enrichment. Country: {country_code}, Mode: {mode}, Filter: {form_filter}")
        
        rows_to_process = catalog.catalog_rows
        
        if form_filter != "All":
            rows_to_process = [row for row in rows_to_process if row.formview_name == form_filter]

        # Group rows by form to process one form at a time
        form_groups = defaultdict(list)
        for row in rows_to_process:
            form_groups[row.xlsform_name].append(row)

        enriched_count = 0
        for form_id, rows in form_groups.items():
            self._logger.log_info(f"Processing form: {form_id}")
            form_context_md = None
            try:
                # Use the provided country_code to build the path
                xls_path_prefix = "muso-mali/forms/app/" if country_code.upper() == "MALI" else "muso-cdi/forms/app/"
                xls_path = f"{xls_path_prefix}{form_id}.xlsx"
                
                self._logger.log_info(f"Downloading XLSForm for context: {xls_path}")
                xls_content = self._code_repo.download_file(branch="master", file_path=xls_path)
                
                form_context_md = self._xlsform_repo.get_survey_sheet_as_markdown(xls_content)
                self._logger.log_info(f"Successfully generated Markdown context for {form_id}")

            except Exception as e:
                self._logger.log_exception(f"Could not get form context for '{form_id}'. Skipping enrichment for this form. Error: {e}")
                continue # Skip to the next form if context can't be loaded

            # Now, iterate through the rows for this specific form
            for row in rows:
                if row.odk_type == 'calculate' and row.calculation:
                    should_process = (mode == "overwrite") or (mode == "fill" and not row.label_fr)

                    if should_process:
                        try:
                            self._logger.log_info(f"Enriching row: {row.column_name} with formula: {row.calculation}")
                            descriptions = self._semantic_repo.get_formula_description_with_context(
                                formula=row.calculation,
                                form_context=form_context_md
                            )
                            
                            row.label_fr = descriptions.get('fr', row.label_fr)
                            row.label_en = descriptions.get('en', row.label_en)
                            row.label_bm = descriptions.get('bm', row.label_bm)
                            enriched_count += 1

                        except Exception as e:
                            self._logger.log_exception(f"Failed to enrich row for column '{row.column_name}': {e}")

        self._logger.log_info(f"Enrichment complete. Processed {enriched_count} rows.")
        return catalog
