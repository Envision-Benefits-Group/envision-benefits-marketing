import logging
import os

import structlog
from structlog.contextvars import merge_contextvars


def setup_logging():
    """
    Configures the logging for the application using structlog.
    """
    # Ensure the logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Set up basic file logging with the built-in logging module
    logging.basicConfig(
        filename="logs/app.log",  # Log file location
        level=logging.INFO,
        format="%(message)s",
        force=True,
    )

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