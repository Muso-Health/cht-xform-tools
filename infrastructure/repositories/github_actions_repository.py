import requests
import os
import sys
from typing import List
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.cicd_repository import CICDRepository
from domain.contracts.logger import Logger
from application.dtos import WorkflowRunDTO

class GitHubActionsRepository(CICDRepository):
    """
    An implementation of the CICDRepository contract that interacts with the GitHub Actions API.
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
        self._logger.log_info(f"GitHubActionsRepository initialized for {self._owner}/{self._repo_name}")

    def get_workflow_runs(self, branch: str = None, workflow_name: str = None) -> List[WorkflowRunDTO]:
        self._logger.log_info(f"Fetching workflow runs for branch: {branch}")
        all_runs_data = []
        per_page = 100
        page = 1
        total_pages = 1

        while page <= total_pages:
            url = f"{self._api_base_url}/actions/runs"
            params = {'per_page': per_page, 'page': page}
            if branch: params['branch'] = branch
            if workflow_name: params['workflow_id'] = workflow_name

            try:
                response = requests.get(url, headers=self._headers, params=params)
                response.raise_for_status()
                response_json = response.json()

                if page == 1:
                    total_count = response_json.get('total_count', 0)
                    total_pages = math.ceil(total_count / per_page)
                    self._logger.log_info(f"Found {total_count} total runs across {total_pages} pages.")

                current_page_runs = response_json.get('workflow_runs', [])
                all_runs_data.extend(current_page_runs)
                page += 1

            except requests.exceptions.HTTPError as e:
                self._logger.log_error(f"HTTP error getting workflow runs: {e}")
                raise Exception(f"HTTP error {e.response.status_code} occurred while getting workflow runs: {e}") from e
            except requests.exceptions.RequestException as e:
                self._logger.log_error(f"Network error getting workflow runs: {e}")
                raise Exception(f"A network error occurred while getting workflow runs: {e}") from e
        
        runs = []
        for item in all_runs_data:
            actor_data = item.get('actor', {})
            dto = WorkflowRunDTO(
                id=item.get('id'),
                name=item.get('name'),
                display_title=item.get('display_title'),
                head_branch=item.get('head_branch'),
                head_sha=item.get('head_sha'),
                status=item.get('status'),
                conclusion=item.get('conclusion'),
                actor_login=actor_data.get('login'),
                actor_avatar=actor_data.get('avatar_url'),
                created_at=item.get('created_at'),
                html_url=item.get('html_url')
            )
            runs.append(dto)
        
        self._logger.log_info(f"Successfully parsed {len(runs)} workflow runs.")
        return runs
