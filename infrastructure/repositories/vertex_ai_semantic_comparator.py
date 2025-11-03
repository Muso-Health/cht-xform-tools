import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.semantic_comparator_repository import SemanticComparatorRepository
from domain.contracts.logger import Logger
from google import genai
from google.genai import types

class VertexAISemanticComparator(SemanticComparatorRepository):
    """
    An implementation of the SemanticComparatorRepository that uses the new Google Gen AI SDK.
    """

    def __init__(self, logger: Logger):
        self._logger = logger
        self._client = genai.Client(vertexai=True, project='musohealth')
        self._model_id = "gemini-2.5-flash"
        self._config = types.GenerateContentConfig(
            max_output_tokens=1024
        )

    def are_titles_semantically_similar(self, title1: str, title2: str) -> bool:
        if not title1 or not title2:
            return False

        prompt = f"""You are an expert in French language. 
        Consider the following two field labels written in French:
        Label 1: '{title1}'
        Label 2: '{title2}'
        Do these two labels refer to the same concept, even if the wording is different? 
        Answer only with 'YES' or 'NO'."""

        try:
            response = self._client.models.generate_content(
                model=self._model_id,
                contents=[prompt],
                config=self._config
            )
            return "YES" in response.text.upper()
        except Exception as e:
            self._logger.log_error(f"An error occurred while calling Vertex AI for title comparison: {e}")
            return False

    def are_formulas_semantically_similar(self, formula1: str, formula2: str) -> bool:
        if not formula1 or not formula2:
            return False

        prompt = f"""You are an ODK XForm expert and developer.
        You are comparing two calculation formulas from two calculate type fields of a form. 
        The syntax is ODK XForms.
        Formula 1: '{formula1}'
        Formula 2: '{formula2}'
        Do these two formulas achieve the same result, even if the formulas are different? 
        Answer only with 'YES' or 'NO'."""

        try:
            response = self._client.models.generate_content(
                model=self._model_id,
                contents=[prompt],
                config=self._config
            )
            return "YES" in response.text.upper()
        except Exception as e:
            self._logger.log_error(f"An error occurred while calling Vertex AI for formula comparison: {e}")
            return False
