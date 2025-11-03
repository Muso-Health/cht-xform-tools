from abc import ABC, abstractmethod

class Logger(ABC):
    """
    Defines a simple, abstract contract for a logging utility.
    This allows the application to be decoupled from any specific logging implementation.
    """

    @abstractmethod
    def log_info(self, message: str):
        """Logs an informational message."""
        pass

    @abstractmethod
    def log_warning(self, message: str):
        """Logs a warning message."""
        pass

    @abstractmethod
    def log_error(self, message: str):
        """Logs an error message."""
        pass

    @abstractmethod
    def log_exception(self, message: str):
        """
        Logs an error message along with the current exception's traceback.
        This should be called from within an `except` block.
        """
        pass
