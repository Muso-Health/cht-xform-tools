from abc import ABC, abstractmethod

class SemanticComparatorRepository(ABC):
    """
    Defines the contract for a repository that can perform semantic comparisons,
    typically by using an external AI/ML model.
    """

    @abstractmethod
    def are_titles_semantically_similar(self, title1: str, title2: str) -> bool:
        """
        Compares two strings (e.g., question titles) for semantic similarity.

        Args:
            title1 (str): The first title.
            title2 (str): The second title.

        Returns:
            bool: True if the titles are considered semantically similar, False otherwise.
        """
        pass

    @abstractmethod
    def are_formulas_semantically_similar(self, formula1: str, formula2: str) -> bool:
        """
        Compares two calculation formulas for semantic similarity.

        Args:
            formula1 (str): The first calculation string.
            formula2 (str): The second calculation string.

        Returns:
            bool: True if the formulas are considered to have the same logical result, False otherwise.
        """
        pass
