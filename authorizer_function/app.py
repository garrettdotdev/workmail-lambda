# authorizer_function/app.py
import json
import logging
import os
from workmail_common.utils import (
    handle_error,
    get_secret_value,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Main handler for Api Gateway authorizer"""
    logger.info(f"Received request: " + json.dumps(event))

    token = event["headers"].get("Authorization")
    if not token:
        logger.warning("No token provided")
        return {"isAuthorized": False}

    # Remove 'Bearer ' from token if present
    if token.lower().startswith("bearer "):
        token = token[7:]

    try:
        secret_name = os.getenv("TOKEN_SECRET_NAME")
        if not secret_name:
            logger.error("TOKEN_SECRET_NAME environment variable not set")
            return {"isAuthorized": False}

        secret = get_secret_value(secret_name)

        if token != secret:
            logger.warning("Invalid token")
            return {"isAuthorized": False}

        return {"isAuthorized": True}

    except Exception as e:
        return handle_error(e)
