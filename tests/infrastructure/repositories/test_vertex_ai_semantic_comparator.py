import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from infrastructure.repositories.vertex_ai_semantic_comparator import VertexAISemanticComparator

# --- Unit Tests ---

@pytest.mark.parametrize(
    "title1, title2, mock_ai_response, expected_result",
    [
        ("Quel est l'âge du patient?", "Quel est l'âge du patient?", "YES", True),
        ("Nom du patient", "Date de la visite", "NO", False),
        ("Date de naissance du patient", "Quelle est la date de naissance de la personne?", "YES", True),
    ]
)
@patch('infrastructure.repositories.vertex_ai_semantic_comparator.genai.Client')
def test_are_titles_semantically_similar_unit(mock_genai_client, title1, title2, mock_ai_response, expected_result):
    mock_response = MagicMock()
    mock_response.text = mock_ai_response
    mock_genai_client.return_value.models.generate_content.return_value = mock_response
    
    comparator = VertexAISemanticComparator()
    result = comparator.are_titles_semantically_similar(title1, title2)
    
    assert result == expected_result
    mock_genai_client.return_value.models.generate_content.assert_called_once()


# --- Integration Test (with enhanced debugging) ---

@pytest.mark.integration
def test_are_titles_semantically_similar_integration():
    try:
        comparator = VertexAISemanticComparator()
    except Exception as e:
        pytest.skip(f"Skipping integration test: GCP authentication failed. Error: {e}")

    title1 = "Aprés demain je voyage à Paris"
    title2 = "je mange bien"

    result = comparator.are_titles_semantically_similar(title1, title2)

    # This assertion will now fail with the exact text from the AI
    assert result is True
