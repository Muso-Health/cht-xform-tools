import pytest
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from infrastructure.repositories.regex_sql_parser_repository import RegexSQLParserRepository
from application.dtos import ParsedColumnDTO

@pytest.mark.parametrize(
    "sql_content, expected_results",
    [
        # Test case 1: Simple JSON_VALUE extraction
        (
            """
            SELECT
                JSON_VALUE(f.doc, '$.form.name') AS form_name,
                JSON_VALUE(f.doc, '$.patient_id') AS patient_id
            FROM my_table f
            """,
            [
                ParsedColumnDTO(column_name='form_name', json_path='$.form.name', sql_type='STRING'),
                ParsedColumnDTO(column_name='patient_id', json_path='$.patient_id', sql_type='STRING')
            ]
        ),
        # Test case 2: SAFE_CAST with JSON_VALUE
        (
            """
            SELECT
                SAFE_CAST(JSON_VALUE(f.doc, '$.form.age') AS INT64) AS patient_age,
                SAFE_CAST(JSON_VALUE(f.doc, '$.form.is_active') AS BOOL) AS is_active
            FROM my_table f
            """,
            [
                ParsedColumnDTO(column_name='patient_age', json_path='$.form.age', sql_type='INT64'),
                ParsedColumnDTO(column_name='is_active', json_path='$.form.is_active', sql_type='BOOL')
            ]
        ),
        # Test case 3: Mix of simple and casted extractions
        (
            """
            SELECT
                JSON_VALUE(f.doc, '$.name') AS patient_name,
                SAFE_CAST(JSON_VALUE(f.doc, '$.dob') AS DATE) AS date_of_birth
            FROM my_table f
            """,
            [
                ParsedColumnDTO(column_name='patient_name', json_path='$.name', sql_type='STRING'),
                ParsedColumnDTO(column_name='date_of_birth', json_path='$.dob', sql_type='DATE')
            ]
        ),
        # Test case 4: Empty SQL string
        ("", []),
        # Test case 5: SQL string with no JSON extractions
        ("SELECT id, name FROM my_table", []),
        # Test case 6: JSON_EXTRACT_SCALAR (older BigQuery syntax)
        (
            """
            SELECT
                JSON_EXTRACT_SCALAR(f.doc, '$.form.id') AS form_id
            FROM my_table f
            """,
            [
                ParsedColumnDTO(column_name='form_id', json_path='$.form.id', sql_type='STRING')
            ]
        ),
        # Test case 7: Overlapping patterns (SAFE_CAST should take precedence)
        (
            """
            SELECT
                JSON_VALUE(f.doc, '$.name') AS patient_name,
                SAFE_CAST(JSON_VALUE(f.doc, '$.name') AS STRING) AS patient_name
            FROM my_table f
            """,
            [
                ParsedColumnDTO(column_name='patient_name', json_path='$.name', sql_type='STRING')
            ]
        ),
    ]
)
def test_parse_columns(sql_content, expected_results):
    # Arrange
    parser = RegexSQLParserRepository()

    # Act
    results = parser.parse_columns(sql_content)

    # Assert
    # Sort both lists to ensure comparison is order-independent
    sorted_results = sorted(results, key=lambda x: x.column_name)
    sorted_expected = sorted(expected_results, key=lambda x: x.column_name)
    
    assert sorted_results == sorted_expected
