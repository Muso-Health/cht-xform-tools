import pytest
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from domain.entities.RichCHTElement import RichCHTElement

def test_rich_element_stores_titles_and_calculation():
    """Tests that the RichCHTElement correctly stores all its properties."""
    # Arrange
    titles = {"fr": "Titre FR", "en": "Title EN"}
    calculation = "1 + 1"

    # Act
    element = RichCHTElement(
        question_name="q1",
        group=False,
        odk_type="calculate",
        path="/data/q1",
        excel_line_number=1,
        titles=titles,
        calculation=calculation
    )

    # Assert
    assert element.question_name == "q1"
    assert element.titles == titles
    assert element.calculation == calculation
    assert element.json_path == "$.fields.q1"

def test_rich_element_handles_none_for_optionals():
    """Tests that the entity handles None for optional fields gracefully."""
    # Act
    element = RichCHTElement(
        question_name="q2",
        group=False,
        odk_type="text",
        path="/data/q2",
        excel_line_number=2
    )

    # Assert
    assert element.titles == {}
    assert element.calculation is None
