import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from application.services.data_catalog_service_impl import DataCatalogServiceImpl
from application.dtos import ParsedColumnDTO, DataCatalogRowDTO, DataCatalogResultDTO
from domain.entities.RichCHTElement import RichCHTElement

@pytest.fixture
def mock_dependencies():
    """Pytest fixture to create mock dependencies for the service."""
    return {
        "cht_app_repo": MagicMock(),
        "code_repo": MagicMock(),
        "dw_repo": MagicMock(),
        "xlsform_repo": MagicMock(),
        "sql_parser_repo": MagicMock(),
        "logger": MagicMock()
    }

def test_generate_catalog_happy_path(mock_dependencies):
    # Arrange
    service = DataCatalogServiceImpl(**mock_dependencies)

    # Mock repository responses
    mock_dependencies["cht_app_repo"].get_installed_xform_ids.return_value = ["form_a"]
    mock_dependencies["code_repo"].download_file.return_value = b"xls_content"
    mock_dependencies["dw_repo"].get_view_query.return_value = "sql_content"
    
    mock_xls_elements = [
        RichCHTElement(
            question_name="patient_name",
            group=False,
            odk_type="text",
            path="/data/patient_name",
            excel_line_number=1,
            titles={"French (fr)": "Nom du patient", "English (en)": "Patient Name"}
        )
    ]
    mock_dependencies["xlsform_repo"].get_rich_elements_from_file.return_value = mock_xls_elements
    
    mock_sql_columns = [
        ParsedColumnDTO(column_name="patient_name", json_path="$.data.patient_name", sql_type="STRING")
    ]
    mock_dependencies["sql_parser_repo"].parse_columns.return_value = mock_sql_columns

    # Act
    result = service.generate_catalog("MALI")

    # Assert
    assert len(result.catalog_rows) == 1
    row = result.catalog_rows[0]
    assert row.xlsform_name == "form_a"
    assert row.column_name == "patient_name"
    assert row.json_path == "$.data.patient_name"
    assert row.label_fr == "Nom du patient"
    assert row.label_en == "Patient Name"
    
    # Verify that all mocks were called as expected
    mock_dependencies["cht_app_repo"].get_installed_xform_ids.assert_called_once_with("MALI")
    mock_dependencies["code_repo"].download_file.assert_called_once()
    mock_dependencies["dw_repo"].get_view_query.assert_called_once()
    mock_dependencies["xlsform_repo"].get_rich_elements_from_file.assert_called_once_with(b"xls_content")
    mock_dependencies["sql_parser_repo"].parse_columns.assert_called_once_with("sql_content")
    mock_dependencies["logger"].log_info.assert_called()

def test_generate_catalog_handles_filenotfound_gracefully(mock_dependencies):
    # Arrange
    service = DataCatalogServiceImpl(**mock_dependencies)
    
    mock_dependencies["cht_app_repo"].get_installed_xform_ids.return_value = ["form_a", "form_b"]
    # Let the first form succeed and the second one fail
    mock_dependencies["code_repo"].download_file.side_effect = [b"xls_content", FileNotFoundError("File not found for form_b")]
    mock_dependencies["dw_repo"].get_view_query.return_value = "sql_content"
    mock_dependencies["xlsform_repo"].get_rich_elements_from_file.return_value = []
    mock_dependencies["sql_parser_repo"].parse_columns.return_value = []

    # Act
    result = service.generate_catalog("MALI")

    # Assert
    # The service should not crash and should complete the audit for the first form
    assert mock_dependencies["code_repo"].download_file.call_count == 2
    # A warning should be logged for the skipped form
    mock_dependencies["logger"].log_warning.assert_called_with("Skipping form 'form_b': Artifact not found. Reason: File not found for form_b")
    # The final result should be empty as we didn't mock a successful correlation
    assert len(result.catalog_rows) == 0

def test_generate_catalog_handles_unmatched_sql_columns(mock_dependencies):
    # Arrange
    service = DataCatalogServiceImpl(**mock_dependencies)

    mock_dependencies["cht_app_repo"].get_installed_xform_ids.return_value = ["form_a"]
    mock_dependencies["code_repo"].download_file.return_value = b"xls_content"
    mock_dependencies["dw_repo"].get_view_query.return_value = "sql_content"
    
    # XLSForm has one element
    mock_xls_elements = [RichCHTElement(question_name="patient_name", path="/data/patient_name", odk_type="text", group=False, excel_line_number=1)]
    mock_dependencies["xlsform_repo"].get_rich_elements_from_file.return_value = mock_xls_elements
    
    # SQL has a column with a JSON path that does NOT match the XLSForm element
    mock_sql_columns = [ParsedColumnDTO(column_name="unrelated_column", json_path="$.data.some_other_field", sql_type="STRING")]
    mock_dependencies["sql_parser_repo"].parse_columns.return_value = mock_sql_columns

    # Act
    result = service.generate_catalog("MALI")

    # Assert
    # No catalog rows should be generated because the paths don't match
    assert len(result.catalog_rows) == 0
    # A warning should be logged about the unmatched column
    mock_dependencies["logger"].log_warning.assert_called_with("Could not find matching XLSForm element for column 'unrelated_column' with path '$.data.some_other_field' in form 'form_a'")
