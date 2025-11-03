from google.cloud import bigquery
from google.api_core import exceptions
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.logger import Logger

class BigQueryRepository(DataWarehouseRepository):
    """
    An implementation of the DataWarehouseRepository that interacts with Google BigQuery.
    """

    def __init__(self, logger: Logger):
        self._logger = logger
        try:
            self._client = bigquery.Client()
            self._logger.log_info("BigQuery client initialized successfully.")
        except Exception as e:
            self._logger.log_exception("Failed to initialize BigQuery client.")
            raise Exception(f"Failed to initialize BigQuery client. Ensure you are authenticated. Error: {e}")

    def get_view_query(self, project_id: str, dataset_id: str, view_id: str) -> str:
        if not all([project_id, dataset_id, view_id]):
            raise ValueError("Project ID, Dataset ID, and View ID cannot be empty.")

        view_ref = f"{project_id}.{dataset_id}.{view_id}"
        self._logger.log_info(f"Fetching view query for: {view_ref}")

        try:
            view = self._client.get_table(view_ref)
            if view.view_query is None:
                raise TypeError(f"The object '{view_ref}' is not a view.")
            return view.view_query

        except exceptions.NotFound:
            self._logger.log_warning(f"The view '{view_ref}' was not found in BigQuery.")
            raise FileNotFoundError(f"The view '{view_ref}' was not found in BigQuery.")
        except exceptions.GoogleAPICallError as e:
            self._logger.log_error(f"An API error occurred while fetching view '{view_ref}': {e}")
            raise Exception(f"An API error occurred while fetching the view: {e}") from e
