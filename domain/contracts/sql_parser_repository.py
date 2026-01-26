from abc import ABC, abstractmethod
from typing import List
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.dtos import ParsedColumnDTO

class SQLParserRepository(ABC):
    """
    Defines the contract for a repository that can parse SQL content.
    """

    @abstractmethod
    def parse_columns(self, sql_content: str) -> List[ParsedColumnDTO]:
        """
        Parses SQL content to extract column information.

        Args:
            sql_content (str): The SQL query string to parse.

        Returns:
            List[ParsedColumnDTO]: A list of objects representing the parsed columns.
        """
        pass
