import requests
import os
import sys
import google.auth
import google.auth.transport.requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.xform_api_repository import XFormApiRepository
from domain.contracts.logger import Logger

class CloudFunctionXFormApiRepository(XFormApiRepository):
    """
    An implementation of the XFormApiRepository contract that interacts with Google Cloud Functions.
    """

    def __init__(self, logger: Logger):
        self._logger = logger
        self._base_urls = {
            "mali": "https://us-central1-musohealth.cloudfunctions.net/gcf-xform-question",
            "rci": "https://us-central1-musohealth.cloudfunctions.net/gcf-xform-question-rci"
        }
        self._requester = google.auth.transport.requests.Request()

    def _get_id_token(self, audience: str) -> str:
        # ... (omitted for brevity, no changes here)
        credentials, project = google.auth.default(scopes=['openid'])
        credentials.refresh(self._requester)
        id_token = credentials.id_token
        if id_token is None:
            credentials.refresh(self._requester)
            id_token = credentials.id_token
            if id_token is None:
                raise Exception("Could not obtain Google ID token.")
        return id_token

    def get_bigquery_extraction_sql(self, country_code: str, xml_name: str) -> str:
        country_code_lower = country_code.lower()
        if country_code_lower not in self._base_urls:
            raise ValueError(f"Invalid country code: {country_code}. Must be 'MALI' or 'RCI'.")

        url = self._base_urls[country_code_lower]
        try:
            self._logger.log_info(f"Fetching SQL from Cloud Function for {xml_name} in {country_code}")
            id_token = self._get_id_token(audience=url)
            headers = {"Authorization": f"Bearer {id_token}", "Content-Type": "application/json"}
            payload = {"xml_name": xml_name, "bigquery_extraction": True}

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_json = response.json()
            sql_code = response_json.get('bigquery_extraction', [None])[0]

            if sql_code is None:
                raise Exception(f"API response did not contain 'bigquery_extraction' SQL for {xml_name}.")

            self._logger.log_info(f"Successfully fetched SQL for {xml_name}.")
            return sql_code

        except requests.exceptions.HTTPError as e:
            self._logger.log_error(f"HTTP error calling Cloud Function: {e}")
            raise Exception(f"HTTP error calling Cloud Function: {e}") from e
        except Exception as e:
            self._logger.log_exception(f"An unexpected error occurred in CloudFunctionXFormApiRepository: {e}")
            raise
