import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from domain.contracts.logger import Logger
from infrastructure.logging.json_formatter import JSONFormatter

class CloudRunLogger(Logger):
    """
    A concrete implementation of the Logger contract that produces structured JSON logs
    suitable for Google Cloud Run and Cloud Logging.
    """

    def __init__(self, level: int = logging.INFO):
        self._logger = logging.getLogger("app") # Get a named logger
        self._logger.setLevel(level)
        self._logger.propagate = False # Prevent duplicate logs in some environments

        # Configure the logger only if it hasn't been configured already
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter())
            self._logger.addHandler(handler)

    def log_info(self, message: str):
        self._logger.info(message)

    def log_warning(self, message: str):
        self._logger.warning(message)

    def log_error(self, message: str):
        self._logger.error(message)

    def log_exception(self, message: str):
        # The `exc_info=True` argument tells the logger to automatically capture the traceback
        self._logger.error(message, exc_info=True)
