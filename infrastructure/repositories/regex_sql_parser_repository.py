import re
from typing import List
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.sql_parser_repository import SQLParserRepository
from application.dtos import ParsedColumnDTO

class RegexSQLParserRepository(SQLParserRepository):
    """
    A concrete implementation of the SQLParserRepository that uses regular expressions
    to parse SQL content and extract column information.
    """

    def __init__(self):
        # This pattern handles extractions with an explicit SAFE_CAST, capturing the type.
        # e.g., SAFE_CAST(JSON_VALUE(f.doc, '$.path.to.field') AS STRING) AS column_name
        self.pattern_with_cast = re.compile(
            r"SAFE_CAST\s*\(\s*JSON_(?:VALUE|EXTRACT_SCALAR)\s*\([^,]+,\s*'([^']+)'\s*\)\s+AS\s+([A-Z0-9_]+)\s*\)\s+AS\s+([a-zA-Z0-9_]+)",
            re.IGNORECASE
        )

        # This pattern handles simple extractions without a cast.
        # e.g., JSON_VALUE(f.doc, '$.path.to.field') AS column_name
        self.pattern_simple = re.compile(
            r"JSON_(?:VALUE|EXTRACT_SCALAR)\s*\([^,]+,\s*'([^']+)'\s*\)\s+AS\s+([a-zA-Z0-9_]+)",
            re.IGNORECASE
        )

    def parse_columns(self, sql_content: str) -> List[ParsedColumnDTO]:
        """
        Parses SQL content to extract column information using two regex patterns.
        It prioritizes matches with explicit casts to get the data type.
        """
        parsed_columns = {}

        # First pass: Find all matches with an explicit SAFE_CAST to get the SQL type.
        matches_with_cast = self.pattern_with_cast.findall(sql_content)
        for match in matches_with_cast:
            json_path, sql_type, column_name = match
            parsed_columns[column_name.lower()] = ParsedColumnDTO(
                column_name=column_name,
                json_path=json_path,
                sql_type=sql_type.upper()
            )

        # Second pass: Find all simple matches.
        matches_simple = self.pattern_simple.findall(sql_content)
        for match in matches_simple:
            json_path, column_name = match
            # Only add if this column hasn't already been parsed by the more specific regex.
            if column_name.lower() not in parsed_columns:
                parsed_columns[column_name.lower()] = ParsedColumnDTO(
                    column_name=column_name,
                    json_path=json_path,
                    sql_type='STRING'  # Default to STRING as type is not specified
                )

        return list(parsed_columns.values())
