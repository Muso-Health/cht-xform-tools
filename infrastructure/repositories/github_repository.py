import requests
import os
import base64
import sys
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.code_repository import CodeRepository
from domain.contracts.logger import Logger
from application.dtos import CommitDTO

class GitHubRepository(CodeRepository):
    """
    An implementation of the CodeRepository contract that interacts with a GitHub repository.
    """

    def __init__(self, owner: str, repo_name: str, logger: Logger):
        self._logger = logger
        self._owner = owner
        self._repo_name = repo_name
        self._token = os.getenv("GITHUB_PAT")
        
        if not self._token:
            raise ValueError("The GITHUB_PAT environment variable is not set.")

        self._api_base_url = f"https://api.github.com/repos/{self._owner}/{self._repo_name}"
        self._headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/vnd.github.v3+json"}
        self._logger.log_info(f"GitHubRepository initialized for {self._owner}/{self._repo_name}")

    def download_file(self, branch: str, file_path: str) -> bytes:
        if not branch or not file_path:
            raise ValueError("Branch and file path cannot be empty.")

        url = f"{self._api_base_url}/contents/{file_path}?ref={branch}"
        self._logger.log_info(f"Downloading file from GitHub: {url}")
        try:
            response = requests.get(url, headers=self._headers)
            response.raise_for_status()
            response_json = response.json()
            
            if "content" not in response_json:
                raise Exception(f"API response for {file_path} did not contain a 'content' field.")

            file_content_base64 = response_json['content']
            return base64.b64decode(file_content_base64)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self._logger.log_warning(f"File not found in GitHub repo: {file_path}")
                raise FileNotFoundError(f"File '{file_path}' not found in branch '{branch}'.") from e
            else:
                self._logger.log_error(f"HTTP error downloading from GitHub: {e}")
                raise Exception(f"HTTP error {e.response.status_code} occurred while downloading file: {e}") from e
        except requests.exceptions.RequestException as e:
            self._logger.log_error(f"Network error downloading from GitHub: {e}")
            raise Exception(f"A network error occurred while downloading file: {e}") from e

    def get_file_history(self, branch: str, file_path: str) -> List[CommitDTO]:
        # ... (implementation remains the same, can add logging if needed)
        return []
