from abc import ABC, abstractmethod
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.dtos import DataCatalogResultDTO

class DataCatalogEnrichmentService(ABC):
    """
    Defines the contract for a service that enriches a data catalog
    by generating descriptions for calculated fields using AI.
    """

    @abstractmethod
    def enrich_catalog(
        self, 
        catalog: DataCatalogResultDTO, 
        country_code: str,
        mode: str, 
        form_filter: str
    ) -> DataCatalogResultDTO:
        """
        Enriches a data catalog by generating descriptions for calculated fields.

        Args:
            catalog (DataCatalogResultDTO): The existing data catalog to enrich.
            country_code (str): The country code (e.g., "MALI" or "RCI").
            mode (str): The generation mode ("fill" or "overwrite").
            form_filter (str): The specific form_view to filter on, or "All".

        Returns:
            DataCatalogResultDTO: The same catalog object, with rows modified in place.
        """
        pass
