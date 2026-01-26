from abc import ABC, abstractmethod
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.dtos import DataCatalogResultDTO

class DataCatalogService(ABC):
    """
    Defines the contract for the service that generates a data catalog.
    """

    @abstractmethod
    def generate_catalog(self, country_code: str) -> DataCatalogResultDTO:
        """
        Orchestrates the generation of a data catalog for a given country.

        Args:
            country_code (str): The country code (e.g., 'MALI', 'RCI').

        Returns:
            DataCatalogResultDTO: An object containing the generated catalog rows.
        """
        pass
