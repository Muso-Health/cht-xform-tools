import pytest
import sys
import os
from typing import List

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from application.services.xlsform_comparator_service_impl import XLSFormComparatorServiceImpl
from domain.contracts.rich_xlsform_repository import RichXLSFormRepository
from domain.contracts.semantic_comparator_repository import SemanticComparatorRepository
from domain.entities.RichCHTElement import RichCHTElement

# --- FAKE REPOSITORIES ---

class FakeRichXLSFormRepository(RichXLSFormRepository):
    def __init__(self, old_elements, new_elements):
        self._old = old_elements
        self._new = new_elements

    def get_rich_elements_from_file(self, file_content: bytes) -> List[RichCHTElement]:
        # Distinguish by checking if the byte content is for old or new
        if file_content == b'old':
            return self._old
        return self._new

class FakeSemanticComparator(SemanticComparatorRepository):
    def are_titles_semantically_similar(self, title1: str, title2: str) -> bool:
        # Simulate a positive match only for a specific pair
        return title1 == "Old Title" and title2 == "New Reworded Title"

    def are_formulas_semantically_similar(self, formula1: str, formula2: str) -> bool:
        return formula1 == "1+1" and formula2 == "2-1"

# --- TEST CASES ---

def test_compare_finds_moved_and_new_deleted_elements():
    # Arrange
    old_elements = [
        RichCHTElement("q1", False, "text", "/data/g1/q1", 1, {"fr": "T1"}), # Moved
        RichCHTElement("q2", False, "text", "/data/q2", 2, {"fr": "T2"}), # Deleted
    ]
    new_elements = [
        RichCHTElement("q1", False, "text", "/data/g2/q1", 1, {"fr": "T1"}), # Moved
        RichCHTElement("q3", False, "text", "/data/q3", 3, {"fr": "T3"}), # New
    ]

    service = XLSFormComparatorServiceImpl(
        xlsform_repo=FakeRichXLSFormRepository(old_elements, new_elements),
        semantic_repo=FakeSemanticComparator()
    )

    # Act
    result = service.compare_forms(b'old', b'new')

    # Assert
    assert len(result.modified_elements) == 1
    assert result.modified_elements[0].reason == "Moved"
    assert result.modified_elements[0].old_element.path == "/data/g1/q1"
    assert result.modified_elements[0].new_element.path == "/data/g2/q1"

    assert len(result.deleted_elements) == 1
    assert result.deleted_elements[0].question_name == "q2"

    assert len(result.new_elements) == 1
    assert result.new_elements[0].question_name == "q3"

def test_compare_finds_semantic_matches():
    # Arrange
    old_elements = [
        RichCHTElement("q_title", False, "text", "/data/q_title", 1, {"fr": "Old Title"}),
        RichCHTElement("q_calc", False, "calculate", "/data/q_calc", 2, calculation="1+1"),
    ]
    new_elements = [
        RichCHTElement("q_title_new", False, "text", "/data/q_title_new", 1, {"fr": "New Reworded Title"}),
        RichCHTElement("q_calc_new", False, "calculate", "/data/q_calc_new", 2, calculation="2-1"),
    ]

    service = XLSFormComparatorServiceImpl(
        xlsform_repo=FakeRichXLSFormRepository(old_elements, new_elements),
        semantic_repo=FakeSemanticComparator()
    )

    # Act
    result = service.compare_forms(b'old', b'new')

    # Assert
    assert len(result.modified_elements) == 2
    assert result.modified_elements[0].reason == "Reworded (Title Match)"
    assert result.modified_elements[1].reason == "Reworded (Formula Match)"
