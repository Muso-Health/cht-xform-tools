from abc import ABC, abstractmethod
from typing import List

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.entities.RichCHTElement import RichCHTElement

class RichXLSFormRepository(ABC):
    """
    Defines the contract for a repository that can read and parse an XLSForm file
    into a list of rich CHT element objects, including titles and calculations.
    """

    @abstractmethod
    def get_rich_elements_from_file(self, file_content: bytes) -> List[RichCHTElement]:
        """
        Parses the content of an XLSForm file and returns a list of RichCHTElement domain entities.

        Args:
            file_content (bytes): The binary content of the .xlsx file.

        Returns:
            List[RichCHTElement]: A list of rich element objects.
        """
        pass
