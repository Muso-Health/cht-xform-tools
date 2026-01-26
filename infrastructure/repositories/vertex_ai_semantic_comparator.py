import sys
import os
import json
from typing import Dict, Optional

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
            max_output_tokens=16384
        )
        
        # Load the static prompt template for XPath-like formulas
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'xpath_inputs_prompt.txt')
            with open(prompt_path, 'r') as f:
                self._xpath_prompt_template = f.read()
        except FileNotFoundError:
            self._logger.log_error("xpath_input_prompt.txt not found. Contextual prompts will be disabled.")
            self._xpath_prompt_template = None

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

    def get_formula_description_with_context(self, formula: str, form_context: str) -> Dict[str, str]:
        if not formula or not form_context:
            return {"fr": "", "en": "", "bm": ""}

        prompt = f"""
        You are an expert ODK XForms developer. Your task is to explain a calculation formula using the entire form as context.

        The full context of the form's 'survey' sheet is provided below in Markdown format:
        ---
        {form_context}
        ---

        The specific formula you need to describe is:
        `{formula}`

        Based on the context, generate a brief, one-sentence description for each language explaining what this calculated field represents.
        
        Your response MUST be a valid JSON object.
        The JSON object MUST have exactly three keys: "fr", "en", and "bm".
        The value for each key MUST be a simple string. DO NOT use nested objects.

        Correct format example:
        {{
            "fr": "Description in French.",
            "en": "Description in English.",
            "bm": "Description in Bamanankan."
        }}
        """

        json_config = types.GenerateContentConfig(
            max_output_tokens=16384,
            response_mime_type="application/json",
        )
        try:
            self._logger.log_info(f"Generating descriptions for formula: {formula} with full context.")
            response = self._client.models.generate_content(
                model=self._model_id,
                contents=[prompt],
                config=json_config
            )
            
            descriptions = json.loads(response.text)

            self._logger.log_info(f"Generated description (fr): {descriptions.get('fr', '')}")
            return {
                "fr": descriptions.get("fr", ""),
                "en": descriptions.get("en", ""),
                "bm": descriptions.get("bm", "")
            }
        except Exception as e:
            self._logger.log_exception(f"An error occurred while generating descriptions for formula '{formula}': {e}")
            try:
                self._logger.log_error(f"Raw AI response text: {response.text}")
            except:
                pass
            return {"fr": f"Error: {e}", "en": f"Error: {e}", "bm": f"Error: {e}"}

    def generate_descriptions_from_formula(
        self, 
        formula: str, 
        context_description: Optional[str] = None
    ) -> Dict[str, str]:
        # This is the old method, kept to satisfy the abstract class contract.
        if not formula:
            return {"fr": "", "en": "", "bm": ""}

        simplified_formula = formula.replace('""', "'")

        if context_description and self._xpath_prompt_template:
            prompt = self._xpath_prompt_template.format(
                explanation=context_description
            )
            self._logger.log_info(f"using prompt: INPUTS")
        else:
            prompt = f"""
            You are an expert ODK XForms developer. Your task is to explain a calculation formula.

            The formula is:
            `{simplified_formula}`

            Generate a brief, one-sentence description for each language explaining what this calculated field represents.
            
            Your response MUST be a valid JSON object.
            The JSON object MUST have exactly three keys: "fr", "en", and "bm".
            The value for each key MUST be a simple string. DO NOT use nested objects.

            Correct format example:
            {{
                "fr": "Description in French.",
                "en": "Description in English.",
                "bm": "Description in Bamanankan."
            }}
            """
            self._logger.log_info(f"using prompt: STANDARD")

        json_config = types.GenerateContentConfig(
            max_output_tokens=16384,
            response_mime_type="application/json",
        )
        try:
            self._logger.log_info(f"Generating descriptions for simplified formula: {simplified_formula}")
            response = self._client.models.generate_content(
                model=self._model_id,
                contents=[prompt],
                config=json_config
            )
            
            descriptions = json.loads(response.text)

            self._logger.log_info(f"description: {descriptions.get('fr', '')}")
            return {
                "fr": descriptions.get("fr", ""),
                "en": descriptions.get("en", ""),
                "bm": descriptions.get("bm", "")
            }
        except Exception as e:
            self._logger.log_exception(f"An error occurred while generating descriptions for formula '{formula}': {e}")
            try:
                self._logger.log_error(f"Raw AI response text: {response.text}")
            except:
                pass
            return {"fr": f"Error: {e}", "en": f"Error: {e}", "bm": f"Error: {e}"}
