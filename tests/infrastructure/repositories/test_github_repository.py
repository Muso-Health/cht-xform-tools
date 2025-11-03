import pytest
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from infrastructure.repositories.github_repository import GitHubRepository

# This is an integration test and will make a real API call to GitHub.
# It requires a GITHUB_PAT to be set, even for public repos, due to rate limiting.
@pytest.mark.integration
def test_download_file_from_public_repo():
    """
    Tests that the repository can successfully download a file from a known public repository.
    This test will be skipped if the GITHUB_PAT environment variable is not set.
    """
    if not os.getenv("GITHUB_PAT"):
        pytest.skip("Skipping integration test: GITHUB_PAT environment variable not set.")

    # Arrange: Point to a well-known public repository and file
    repo_owner = "pytest-dev"
    repo_name = "pytest"
    branch = "main"
    file_path = "LICENSE"
    
    repository = GitHubRepository(owner=repo_owner, repo_name=repo_name)

    # Act
    file_content = repository.download_file(branch=branch, file_path=file_path)

    # Assert
    assert file_content is not None
    assert len(file_content) > 0
    # Check for the copyright notice which should be stable
    assert b"MIT License" in file_content
