# authorizer_function/app.py
import json
import logging
import os
from workmail_common.utils import (
    get_aws_clients,
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
        raise Exception("Unauthorized")

    # Remove 'Bearer ' from token if present
    if token.lower.startswith("bearer "):
        token = token[7:]

    try:
        secret_name = os.getenv("TOKEN_SECRET_NAME")
        if not secret_name:
            logger.error("TOKEN_SECRET_NAME environment variable not set")
            raise Exception("Internal Server Error")

        secret = get_secret_value(secret_name)

        if token != secret:
            logger.warning("Invalid token")
            return {"isAuthorized": False}

        return {"isAuthorized": True}

    except Exception as e:
        handle_error(e)
