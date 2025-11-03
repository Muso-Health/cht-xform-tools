from abc import ABC, abstractmethod
from typing import List

class CHTAppRepository(ABC):
    """
    Defines the contract for interacting with a CHT application instance.
    """

    @abstractmethod
    def get_installed_xform_ids(self, country_code: str) -> List[str]:
        """
        Retrieves a list of installed XForm IDs (names without .xml extension)
        from the specified CHT application instance.

        Args:
            country_code (str): The country code (e.g., 'MALI' or 'RCI').

        Returns:
            List[str]: A list of XForm IDs (e.g., ["patient_assessment", "delivery"]).

        Raises:
            Exception: For API-related errors (e.g., auth, network, invalid country).
        """
        pass
