import logging
import os
import sys

import structlog
from structlog.contextvars import merge_contextvars


def setup_logging():
    """
    Configures the logging for the application using structlog.
    Logs are written to both logs/app.log and stdout (terminal).
    """
    # Ensure the logs directory exists
    os.makedirs("logs", exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers on reload
    if not root_logger.handlers:
        fmt = logging.Formatter("%(message)s")

        # File handler — persisted JSON logs
        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(fmt)
        root_logger.addHandler(file_handler)

        # Console handler — visible in terminal
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(fmt)
        root_logger.addHandler(console_handler)

    # Custom processor to rename fields for clarity in logs
    def rename_fields(_, __, event_dict):
        if "event" in event_dict:
            event_dict["message"] = event_dict.pop("event")
        if "logger" in event_dict:
            event_dict["Module"] = event_dict.pop("logger")
        return event_dict

    # Configure structlog for structured, JSON-based logging
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=True),
            rename_fields,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    ) 