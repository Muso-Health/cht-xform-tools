import sys
import os
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.contracts.form_comparator_service import FormComparatorService
from application.dtos import ComparisonResultDTO, FoundReferenceDTO, NotFoundElementDTO
from domain.contracts.xlsform_repository import XLSFormRepository

class FormComparatorServiceImpl(FormComparatorService):
    """
    Concrete implementation of the FormComparatorService.
    """

    def __init__(self, xlsform_repository: XLSFormRepository):
        self._xlsform_repo = xlsform_repository

    def compare_form_with_sql(self, xls_content: bytes, sql_content: bytes, country: str) -> ComparisonResultDTO:
        """
        Compares the elements of an XLSForm with the content of a SQL file.
        """
        # The parser now returns a dictionary; we are interested in the main elements for this comparison.
        parsed_data = self._xlsform_repo.get_elements_from_file(xls_content)
        elements = parsed_data.get("main_elements", [])
        
        sql_content_str = sql_content.decode('utf-8')
        
        founds: List[FoundReferenceDTO] = []
        not_founds: List[NotFoundElementDTO] = []
        not_found_bm_elements: List[NotFoundElementDTO] = []

        for el in elements:
            if el.json_path:
                if el.json_path in sql_content_str:
                    # This part of the logic for 'founds' seems to be unused in the UI,
                    # but we'll keep it for potential future use.
                    pass
                else:
                    # Separate _bm elements for RCI, as they are non-critical
                    if country == 'RCI' and el.question_name.endswith('_bm'):
                        not_found_bm_elements.append(NotFoundElementDTO(element_name=el.question_name, json_path=el.json_path))
                    else:
                        not_founds.append(NotFoundElementDTO(element_name=el.question_name, json_path=el.json_path))

        # For now, we return an empty 'founds' list as the primary goal is to find discrepancies.
        return ComparisonResultDTO(founds=[], not_founds=not_founds, not_found_bm_elements=not_found_bm_elements)
