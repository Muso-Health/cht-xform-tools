import pytest
import sys
import os
from typing import List

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from application.services.bulk_audit_service_impl import BulkAuditServiceImpl
from application.dtos import BulkAuditResultDTO
from domain.contracts.cht_app_repository import CHTAppRepository
from domain.contracts.code_repository import CodeRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.xlsform_repository import XLSFormRepository
from domain.entities.CHTElement import CHTElement

# --- FAKE REPOSITORIES FOR TESTING ---

class FakeCHTAppRepository(CHTAppRepository):
    def get_installed_xform_ids(self, country_code: str) -> List[str]:
        return ["form1_ok", "form2_missing_xls", "form3_missing_view"]

class FakeCodeRepository(CodeRepository):
    def download_file(self, branch: str, file_path: str) -> bytes:
        if "form2_missing_xls" in file_path:
            raise FileNotFoundError(f"File not found: {file_path}")
        return b''

    def get_file_history(self, branch: str, file_path: str) -> List[any]:
        return []

class FakeDataWarehouseRepository(DataWarehouseRepository):
    def get_view_query(self, project_id: str, dataset_id: str, view_id: str) -> str:
        if "form3_missing_view" in view_id:
            raise FileNotFoundError(f"View not found: {view_id}")
        return "SELECT JSON_EXTRACT_SCALAR(doc, '$.fields.group.question') FROM table"

class FakeXLSFormRepository(XLSFormRepository):
    def get_elements_from_file(self, file_content: bytes) -> List[CHTElement]:
        # Updated to include new constructor arguments
        return [
            CHTElement(
                question_name="question", group=False, odk_type="text", 
                path="/data/group/question", excel_line_number=1, 
                titles={"fr": "Question"}, calculation=None
            )
        ]

# --- UNIT TESTS ---

@pytest.fixture
def bulk_audit_service() -> BulkAuditServiceImpl:
    """This pytest fixture creates and injects all the fake repositories into the service."""
    return BulkAuditServiceImpl(
        cht_app_repo=FakeCHTAppRepository(),
        code_repo=FakeCodeRepository(),
        dw_repo=FakeDataWarehouseRepository(),
        xlsform_repo=FakeXLSFormRepository()
    )

def test_perform_audit_identifies_missing_xlsform(bulk_audit_service: BulkAuditServiceImpl):
    """Tests that the audit correctly identifies a form that is missing from the GitHub repo."""
    # Act
    result: BulkAuditResultDTO = bulk_audit_service.perform_audit("MALI")

    # Assert
    assert "form2_missing_xls" in result.missing_xlsforms
    assert len(result.missing_xlsforms) == 1
    assert "form3_missing_view" in result.missing_views
    assert len(result.missing_views) == 1
    assert len(result.compared_forms) == 1
    assert result.compared_forms[0].form_id == "form1_ok"
