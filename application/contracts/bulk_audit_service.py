from abc import ABC, abstractmethod

import sys
import os # <--- Added this import

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.dtos import BulkAuditResultDTO

class BulkAuditService(ABC):
    """
    Defines the contract for the service that performs a bulk audit of all forms.
    """

    @abstractmethod
    def perform_audit(self, country_code: str) -> BulkAuditResultDTO:
        """
        Orchestrates a full audit of a CHT instance.
        1. Fetches all installed forms from the CHT.
        2. For each form, fetches the corresponding XLSForm from GitHub and the BigQuery view.
        3. Compares them to find discrepancies.

        Args:
            country_code (str): The country to audit ('MALI' or 'RCI').

        Returns:
            BulkAuditResultDTO: An object containing the full audit results.
        """
        pass
