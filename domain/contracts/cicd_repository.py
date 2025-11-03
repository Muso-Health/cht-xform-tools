from abc import ABC, abstractmethod
from typing import List

# Add the project root to the Python path to allow for absolute imports from the application layer
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.dtos import WorkflowRunDTO

class CICDRepository(ABC):
    """
    Defines the contract for a CI/CD repository, specifically for GitHub Actions.
    This interface abstracts the methods needed to interact with workflow runs.
    """

    @abstractmethod
    def get_workflow_runs(self, branch: str, workflow_name: str = None) -> List[WorkflowRunDTO]:
        """
        Retrieves a list of GitHub Actions workflow runs for a specific branch.

        Args:
            branch (str): The name of the branch to filter workflow runs by.
            workflow_name (str, optional): The name of the workflow to filter by. Defaults to None.

        Returns:
            List[WorkflowRunDTO]: A list of workflow run data transfer objects.

        Raises:
            Exception: For API-related errors.
        """
        pass
