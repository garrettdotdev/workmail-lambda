import json
import os
import logging
from botocore.exceptions import ClientError, BotoCoreError
from jsonschema.exceptions import ValidationError
from requests import RequestException
from typing import Any, Dict

logger = logging.getLogger(__name__)


def load_schema(schema_path: str) -> Dict[str, Any]:
    try:
        with open(schema_path) as schema_file:
            return json.load(schema_file)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON schema: {e}")
        raise


def handle_error(e: Exception) -> Dict[str, Any]:
    """Handle exceptions."""
    error_mapping = {
        ValidationError: (400, lambda e: f"Invalid input: {e.message}"),
        json.JSONDecodeError: (400, lambda e: "Invalid JSON format"),
        ClientError: (500, lambda e: e.response["Error"]["Message"]),
        BotoCoreError: (500, lambda e: "An unspecified error occurred"),
        ValueError: (400, lambda e: str(e)),
        RequestException: (502, lambda e: "Bad Gateway"),
        KeyError: (400, lambda e: f"Key error: {e.args[0]}"),
    }
    for exception_types, (status_code, message_func) in error_mapping.items():
        if isinstance(e, exception_types):
            logger.error(f"{exception_types.__name__} occurred: {e}")
            return {
                "statusCode": status_code,
                "body": json.dumps({"error": message_func(e)}),
            }
    logger.error(f"Unexpected error occurred: {e}")
    return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
