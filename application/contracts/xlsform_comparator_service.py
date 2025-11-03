from abc import ABC, abstractmethod
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.dtos import XLSFormComparisonResultDTO

class XLSFormComparatorService(ABC):
    """
    Defines the contract for the service that compares two XLSForms.
    """

    @abstractmethod
    def compare_forms(
        self, 
        old_form_content: bytes, 
        new_form_content: bytes, 
        exclude_notes: bool, 
        exclude_inputs: bool, 
        exclude_prescription: bool,
        use_title_matching: bool,
        use_formula_matching: bool
    ) -> XLSFormComparisonResultDTO:
        """
        Orchestrates the comparison between two versions of an XLSForm.

        Args:
            old_form_content (bytes): The binary content of the old XLSForm file.
            new_form_content (bytes): The binary content of the new XLSForm file.
            exclude_notes (bool): If True, elements with odk_type 'note' will be excluded.
            exclude_inputs (bool): If True, elements in the 'inputs' group will be excluded.
            exclude_prescription (bool): If True, elements in the 'prescription_summary' group will be excluded.
            use_title_matching (bool): If True, use AI to find semantically similar titles.
            use_formula_matching (bool): If True, use AI to find semantically similar formulas.

        Returns:
            XLSFormComparisonResultDTO: An object containing the detailed comparison results.
        """
        pass
