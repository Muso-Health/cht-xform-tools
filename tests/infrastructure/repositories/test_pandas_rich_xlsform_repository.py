import pytest
import sys
import os
import io
from openpyxl import Workbook

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from infrastructure.repositories.pandas_rich_xlsform_repository import PandasRichXLSFormRepository

@pytest.fixture
def rich_xlsform_repository() -> PandasRichXLSFormRepository:
    return PandasRichXLSFormRepository()

@pytest.fixture
def rich_xlsform_bytes() -> bytes:
    """Creates a minimal in-memory XLSForm with all new columns and returns its content as bytes."""
    wb = Workbook()
    survey_ws = wb.active
    survey_ws.title = "survey"
    settings_ws = wb.create_sheet("settings")

    settings_ws.append(['form_id'])
    settings_ws.append(['rich_form'])

    survey_ws.append(['type', 'name', 'label::en', 'label::fr', 'label::bm', 'calculation'])
    survey_ws.append(['text', 'q1', 'Q1', 'Q1_FR', 'Q1_BM', ''])
    survey_ws.append(['calculate', 'c1', '', '', '', '1+1'])

    virtual_workbook = io.BytesIO()
    wb.save(virtual_workbook)
    virtual_workbook.seek(0)
    return virtual_workbook.read()

def test_get_rich_elements_parses_correctly(rich_xlsform_repository: PandasRichXLSFormRepository, rich_xlsform_bytes: bytes):
    """Tests that the repository correctly parses a rich XLSForm into RichCHTElement objects."""
    # Act
    elements = rich_xlsform_repository.get_rich_elements_from_file(rich_xlsform_bytes)

    # Assert
    assert len(elements) == 2

    q1 = next(el for el in elements if el.question_name == 'q1')
    c1 = next(el for el in elements if el.question_name == 'c1')

    assert q1.titles['fr'] == "Q1_FR"
    assert q1.calculation is None

    assert c1.odk_type == "calculate"
    assert c1.calculation == "1+1"
    assert c1.titles['en'] == ""
