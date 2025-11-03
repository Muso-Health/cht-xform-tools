from abc import ABC, abstractmethod

class XFormApiRepository(ABC):
    """
    Defines the contract for an API that can generate BigQuery SQL from an XForm definition.
    """

    @abstractmethod
    def get_bigquery_extraction_sql(self, country_code: str, xml_name: str) -> str:
        """
        Retrieves the BigQuery extraction SQL for a given XForm.

        Args:
            country_code (str): The country code (e.g., 'rci' or 'mali').
            xml_name (str): The name of the XForm (without extension).

        Returns:
            str: The generated SQL query string.

        Raises:
            Exception: For API-related errors (e.g., auth, network, not found).
        """
        pass
