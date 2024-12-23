# workmail_common/utils.py
import json
import logging
import re
import boto3
import mysql.connector
import jwt
import fastjsonschema
from botocore.config import Config
from boto3.exceptions import Boto3Error
from botocore.exceptions import (
    BotoCoreError,
    NoCredentialsError,
    PartialCredentialsError,
)
from fastjsonschema import JsonSchemaException
from requests import RequestException
from typing import Any, Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def connect_to_rds(secret_manager_client: Any, config: Dict[str, str]) -> Any:
    try:
        db_secret_arn = config["DB_SECRET_ARN"]
        database_name = config["DATABASE_NAME"]
        db_secret = secret_manager_client.get_secret_value(SecretId=db_secret_arn)
        db_credentials = json.loads(db_secret["SecretString"])

        connection = mysql.connector.connect(
            user=db_credentials["username"],
            password=db_credentials["password"],
            host=db_credentials["host"],
            database=database_name,
        )
        return connection
    except Exception as e:
        raise


def extract_domain(url: str) -> (str, str):
    """
    Extract the full domain and root domain from a given URL or domain string.

    Args:
        url (str): The URL or domain to extract.

    Returns:
        tuple: A tuple containing the full domain (e.g., "blog.example.com") and the root domain (e.g., "example").
    """

    # Parse the URL, and if it lacks a scheme, add 'http://' to ensure it parses correctly
    parsed = urlparse(url if "://" in url else f"http://{url}")
    hostname = parsed.hostname

    if not hostname:
        raise Exception(f"Invalid URL or domain name: '{url}'")

    # Remove www. if present (normalize the hostname)
    hostname = hostname.lstrip("www.")

    # Validate the domain using a regex (ensure it has at least one dot)
    if not re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", hostname):
        raise Exception(f"Invalid domain name: '{hostname}'")

    # Extract the full domain (e.g., blog.example.com)
    full_domain = hostname

    # Extract the root domain (e.g., 'example' from blog.example.com)
    domain_parts = full_domain.split(".")
    if len(domain_parts) >= 2:
        root_domain = domain_parts[-2]
    else:
        raise Exception(f"Unable to extract root domain from: '{full_domain}'")

    return full_domain, root_domain


def get_account_id():
    return boto3.client("sts").get_caller_identity().get("Account")


def get_aws_clients() -> Dict[str, Any]:
    logger.info("Initializing AWS clients")

    client_config = Config(
        connect_timeout=5, retries={"max_attempts": 2, "mode": "adaptive"}
    )

    try:
        return {
            "secretsmanager_client": boto3.client(
                "secretsmanager", config=client_config
            ),
            "ses_client": boto3.client("ses", config=client_config),
            "workmail_client": boto3.client("workmail", config=client_config),
        }
    except Exception as e:
        raise


def get_aws_client(service_name: str) -> boto3.client:
    try:
        client = boto3.client(service_name)
        return client
    except Exception as e:
        raise


def get_secret_value(secret_name: str) -> str:
    """Retrieve the secret value from AWS Secrets Manager."""
    try:
        secretsmanager_client = get_aws_client("secretsmanager")
        response = secretsmanager_client.get_secret_value(SecretId=secret_name)
        secret = response["SecretString"]
        return secret
    except Exception as e:
        raise


def handle_error(e: Exception) -> Dict[str, Any]:
    """Handle exceptions."""
    logger.warning(f"handle_error is attempting to handle a raised exception...")
    error_mapping = {
        json.JSONDecodeError: (400, lambda: "Invalid JSON format"),
        JsonSchemaException: (400, lambda: f"Schema validation error: {str(e)}"),
        ValueError: (400, lambda: str(e)),
        RequestException: (502, lambda: "Bad Gateway"),
        KeyError: (400, lambda: f"Key error: {e.args[0]}"),
        NoCredentialsError: (500, lambda: "No AWS credentials found"),
        PartialCredentialsError: (
            500,
            lambda: "Partial AWS credentials found",
        ),
        jwt.ExpiredSignatureError: (401, lambda: "Token has expired"),
        jwt.InvalidTokenError: (401, lambda: "Invalid token"),
        Boto3Error: (500, lambda: "An unspecified error occurred"),
        BotoCoreError: (500, lambda: "An unspecified error occurred"),
    }
    clients = get_aws_clients()
    for client_name, client in clients.items():
        client_exceptions = {
            getattr(client.exceptions, exception_name): (
                500,
                lambda exception_name=exception_name: f"{exception_name}: {str(e)}",
            )
            for exception_name in dir(client.exceptions)
            if exception_name.endswith("Exception")
        }
        error_mapping.update(client_exceptions)

    for exception_types, (status_code, message_func) in error_mapping.items():
        if isinstance(e, exception_types):
            logger.error(f"{exception_types.__name__} occurred: {e}")
            return {
                "statusCode": status_code,
                "body": json.dumps({"error": message_func()}),
            }
    logger.error(f"Unexpected error occurred: {e}")
    return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


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


def validate(body: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    try:
        validator = fastjsonschema.compile(schema)
        validator(body)
        return True
    except fastjsonschema.JsonSchemaException as e:
        raise


def process_input(body: Dict[str, Any], schemapath: str) -> Dict[str, Any]:
    schema = load_schema(schemapath)
    try:
        validate(body, schema)

        full_domain, root_domain = extract_domain(body["vanity_name"])
        body["vanity_name"] = full_domain
        body["org_name"] = root_domain

        email_address = f"{body['email_username']}@{body['vanity_name']}"
        body["email_address"] = email_address

    except Exception as e:
        raise e

    return body
