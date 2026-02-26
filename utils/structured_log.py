"""
Structured logging with severity and optional JSON. Set LOG_LEVEL (default INFO) and LOG_JSON=true for JSON lines.
"""
import json
import logging
import os

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_LOG_JSON = os.getenv("LOG_JSON", "false").lower() == "true"


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if getattr(record, "request_id", None):
            payload["request_id"] = record.request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(getattr(logging, _LOG_LEVEL, logging.INFO))
    handler = logging.StreamHandler()
    if _LOG_JSON:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(handler)
    return logger
