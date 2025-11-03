import requests
import os
import sys
from typing import List, Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.cht_app_repository import CHTAppRepository
from domain.contracts.logger import Logger

class HttpCHTAppRepository(CHTAppRepository):
    """
    An implementation of the CHTAppRepository that interacts with a CHT instance via HTTP.
    """

    def __init__(self, logger: Logger):
        self._logger = logger
        self._credentials: Dict[str, tuple] = {
            "MALI": (os.getenv("CHT_MALI_USERNAME"), os.getenv("CHT_MALI_PASSWORD")),
            "RCI": (os.getenv("CHT_RCI_USERNAME"), os.getenv("CHT_RCI_PASSWORD"))
        }

        if not all(self._credentials["MALI"]) or not all(self._credentials["RCI"]):
            raise ValueError("CHT_MALI_USERNAME, CHT_MALI_PASSWORD, CHT_RCI_USERNAME, and CHT_RCI_PASSWORD environment variables must all be set.")

        self._base_urls = {
            "MALI": "https://cht.mali.prod.musohealth.app/",
            "RCI": "https://cht.rci.app.musohealth.app/"
        }
        self._endpoint = "api/v1/forms"

    def get_installed_xform_ids(self, country_code: str) -> List[str]:
        country_upper = country_code.upper()
        if country_upper not in self._base_urls:
            raise ValueError(f"Invalid country code: {country_code}. Must be 'MALI' or 'RCI'.")

        url = self._base_urls[country_upper] + self._endpoint
        auth_credentials = self._credentials[country_upper]

        try:
            self._logger.log_info(f"Fetching installed forms from {url}")
            response = requests.get(url, auth=auth_credentials)
            response.raise_for_status()

            form_files = response.json()
            if not isinstance(form_files, list):
                raise TypeError("API response is not a list as expected.")

            form_ids = [f.replace(".xml", "") for f in form_files if isinstance(f, str) and not f.startswith("contact:")]
            self._logger.log_info(f"Found {len(form_ids)} forms.")
            return form_ids

        except requests.exceptions.HTTPError as e:
            self._logger.log_error(f"HTTP error {e.response.status_code} occurred while fetching forms: {e}")
            raise Exception(f"HTTP error {e.response.status_code} occurred while fetching forms: {e}") from e
        except requests.exceptions.RequestException as e:
            self._logger.log_error(f"A network error occurred while fetching forms: {e}")
            raise Exception(f"A network error occurred while fetching forms: {e}") from e
