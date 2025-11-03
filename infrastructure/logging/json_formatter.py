import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    A custom log formatter that outputs log records as a single-line JSON string,
    formatted for consumption by Google Cloud Logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }

        # If the log record contains exception information, format it and add it.
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_object)
