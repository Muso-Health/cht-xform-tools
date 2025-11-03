from abc import ABC, abstractmethod
from typing import List

# Add the project root to the Python path to allow for absolute imports from the application layer
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.dtos import CommitDTO

class CodeRepository(ABC):
    """
    Defines the contract for a code repository, such as one hosted on GitHub.
    This interface abstracts the methods needed to interact with the repository's files.
    """

    @abstractmethod
    def download_file(self, branch: str, file_path: str) -> bytes:
        """
        Downloads a single file from a specific branch of the repository.

        Args:
            branch (str): The name of the branch from which to download the file (e.g., 'main').
            file_path (str): The full path to the file within the repository.

        Returns:
            bytes: The raw content of the downloaded file.

        Raises:
            FileNotFoundError: If the file does not exist in the specified branch.
            Exception: For other download-related errors (e.g., network issues, permissions).
        """
        pass

    @abstractmethod
    def get_file_history(self, branch: str, file_path: str) -> List[CommitDTO]:
        """
        Retrieves the commit history for a specific file on a given branch.

        Args:
            branch (str): The name of the branch where the file resides.
            file_path (str): The full path to the file within the repository.

        Returns:
            A list of CommitDTO objects, ordered from most recent to oldest.

        Raises:
            FileNotFoundError: If the file does not exist in the specified branch.
            Exception: For other API-related errors.
        """
        pass
