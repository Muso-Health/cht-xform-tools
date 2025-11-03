import pytest
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from domain.entities.CHTElement import CHTElement

def test_calculate_json_path_for_standard_field():
    """Tests that a standard nested field path is correctly converted to '$.fields.' format."""
    element = CHTElement(
        question_name="question1", group=False, odk_type="text", 
        path="/data/group1/question1", excel_line_number=1
    )
    assert element.json_path == "$.fields.group1.question1"

def test_calculate_json_path_for_inputs_field():
    """Tests that a field within the 'inputs' group is correctly converted to '$.' format."""
    element = CHTElement(
        question_name="instanceID", group=False, odk_type="calculate", 
        path="/data/inputs/meta/instanceID", excel_line_number=2
    )
    assert element.json_path == "$.inputs.meta.instanceID"

def test_json_path_is_none_for_group():
    """Tests that the json_path is correctly set to None for a group element."""
    element = CHTElement(
        question_name="group1", group=True, odk_type="begin group", 
        path="/data/group1", excel_line_number=3
    )
    assert element.json_path is None

def test_titles_and_calculation_are_stored():
    """Tests that titles and calculation are correctly stored on the element."""
    titles = {"fr": "Titre FR", "en": "Title EN", "bm": "Titre BM"}
    calculation = "coalesce(${a}, ${b})"
    
    element = CHTElement(
        question_name="q1", group=False, odk_type="calculate", 
        path="/data/q1", excel_line_number=4,
        titles=titles,
        calculation=calculation
    )
    
    assert element.titles == titles
    assert element.calculation == calculation

def test_titles_defaults_to_empty_dict_if_none():
    """Tests that the titles attribute defaults to an empty dict if not provided."""
    element = CHTElement(
        question_name="q1", group=False, odk_type="text", 
        path="/data/q1", excel_line_number=5
    )
    assert element.titles == {}
    assert element.calculation is None
