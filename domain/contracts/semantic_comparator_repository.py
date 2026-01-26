from abc import ABC, abstractmethod
from typing import Dict, Optional

class SemanticComparatorRepository(ABC):
    """
    Defines the contract for a repository that can perform semantic comparisons
    and generate content using a generative AI model.
    """

    @abstractmethod
    def are_titles_semantically_similar(self, title1: str, title2: str) -> bool:
        """
        Compares two titles for semantic similarity.

        Args:
            title1 (str): The first title.
            title2 (str): The second title.

        Returns:
            bool: True if the titles are semantically similar, False otherwise.
        """
        pass

    @abstractmethod
    def are_formulas_semantically_similar(self, formula1: str, formula2: str) -> bool:
        """
        Compares two ODK calculation formulas for semantic similarity.

        Args:
            formula1 (str): The first formula.
            formula2 (str): The second formula.

        Returns:
            bool: True if the formulas are semantically similar, False otherwise.
        """
        pass

    @abstractmethod
    def generate_descriptions_from_formula(
        self, 
        formula: str, 
        context_description: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generates multilingual descriptions for a given ODK calculation formula.

        Args:
            formula (str): The ODK calculation formula.
            context_description (Optional[str]): An optional human-readable description
                                                 of the context for CHT-specific formulas.

        Returns:
            Dict[str, str]: A dictionary containing the generated descriptions
                            with keys 'fr', 'en', and 'bm'.
        """
        pass
