import sys
import os
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from domain.contracts.logger import Logger

class DummyLogger(Logger):
    """A logger that does nothing. Used for testing."""

    def log_info(self, message: str):
        pass

    def log_warning(self, message: str):
        pass

    def log_error(self, message: str):
        pass

    def log_exception(self, message: str, exc_info: Optional[bool] = True):
        pass
