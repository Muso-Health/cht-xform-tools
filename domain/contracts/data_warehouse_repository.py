from abc import ABC, abstractmethod

class DataWarehouseRepository(ABC):
    """
    Defines the contract for a data warehouse, such as Google BigQuery.
    This interface abstracts the methods needed to retrieve metadata about
    data warehouse objects, like the definition of a view.
    """

    @abstractmethod
    def get_view_query(self, project_id: str, dataset_id: str, view_id: str) -> str:
        """
        Retrieves the underlying SQL query for a specific view.

        Args:
            project_id (str): The ID of the project containing the view.
            dataset_id (str): The ID of the dataset containing the view.
            view_id (str): The ID of the view.

        Returns:
            str: The SQL query string that defines the view.

        Raises:
            FileNotFoundError: If the specified view does not exist.
            Exception: For other API-related errors (e.g., permissions, network).
        """
        pass
