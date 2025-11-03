from abc import ABC, abstractmethod
from typing import List

# Add the project root to the Python path to allow for absolute imports from the domain layer
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.entities.CHTElement import CHTElement

class XLSFormRepository(ABC):
    """
    Defines the contract for a repository that can read and parse an XLSForm file.
    """

    @abstractmethod
    def get_elements_from_file(self, file_content: bytes) -> List[CHTElement]:
        """
        Parses the content of an XLSForm file and returns a list of CHTElement domain entities.

        Args:
            file_content (bytes): The binary content of the .xlsx file.

        Returns:
            List[CHTElement]: A list of CHTElement objects representing the questions and groups in the form.

        Raises:
            Exception: For parsing-related errors.
        """
        pass
