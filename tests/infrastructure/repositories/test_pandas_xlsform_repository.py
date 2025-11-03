import pytest
import sys
import os
import io
from openpyxl import Workbook

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from infrastructure.repositories.pandas_xlsform_repository import PandasXLSFormRepository
from domain.entities.CHTElement import CHTElement

@pytest.fixture
def xlsform_repository() -> PandasXLSFormRepository:
    """Provides an instance of the repository for testing."""
    return PandasXLSFormRepository()

@pytest.fixture
def rich_xlsform_bytes() -> bytes:
    """Creates a minimal in-memory XLSForm with all new columns and returns its content as bytes."""
    wb = Workbook()
    survey_ws = wb.active
    survey_ws.title = "survey"
    settings_ws = wb.create_sheet("settings")

    settings_ws.append(['form_id'])
    settings_ws.append(['my_test_form'])

    # Include new columns for titles and calculation
    survey_ws.append(['type', 'name', 'label::en', 'label::fr', 'label::bm', 'calculation'])
    survey_ws.append(['text', 'question1', 'Q1', 'Q1_FR', 'Q1_BM', ''])
    survey_ws.append(['begin group', 'group1', 'G1', 'G1_FR', 'G1_BM', ''])
    survey_ws.append(['calculate', 'calc1', '', '', '', 'coalesce(${q1}, 0)'])
    survey_ws.append(['end group', 'group1', '', '', '', ''])

    virtual_workbook = io.BytesIO()
    wb.save(virtual_workbook)
    virtual_workbook.seek(0)
    return virtual_workbook.read()

def test_get_elements_from_file_parses_rich_xlsform(xlsform_repository: PandasXLSFormRepository, rich_xlsform_bytes: bytes):
    """Tests that the repository correctly parses a valid XLSForm including titles and calculation."""
    # Act
    elements = xlsform_repository.get_elements_from_file(rich_xlsform_bytes)

    # Assert
    assert len(elements) == 3 # question1, group1, calc1

    # Test question1
    q1 = next(el for el in elements if el.question_name == 'question1')
    assert q1.titles['en'] == "Q1"
    assert q1.titles['fr'] == "Q1_FR"
    assert q1.titles['bm'] == "Q1_BM"
    assert q1.calculation is None

    # Test group1
    g1 = next(el for el in elements if el.question_name == 'group1')
    assert g1.group is True
    assert g1.titles['en'] == "G1"

    # Test calc1
    c1 = next(el for el in elements if el.question_name == 'calc1')
    assert c1.odk_type == "calculate"
    assert c1.calculation == "coalesce(${q1}, 0)"
    assert c1.titles['fr'] == ""
