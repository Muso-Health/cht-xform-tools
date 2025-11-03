from abc import ABC, abstractmethod

import sys
import os # <--- Added this import

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.dtos import ComparisonResultDTO

class FormComparatorService(ABC):
    """
    Defines the contract for the application service that handles the form comparison logic.
    """

    @abstractmethod
    def compare_form_with_sql(self, xlsform_content: bytes, sql_content: bytes, country_code: str) -> ComparisonResultDTO:
        """
        Orchestrates the comparison between an XLSForm and a SQL file.

        Args:
            xlsform_content (bytes): The binary content of the uploaded XLSForm file.
            sql_content (bytes): The binary content of the uploaded SQL file.
            country_code (str): The country context for applying specific business rules (e.g., 'MALI' or 'RCI').

        Returns:
            ComparisonResultDTO: A data transfer object containing the results of the comparison.
        """
        pass
