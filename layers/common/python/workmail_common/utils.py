import json
import logging
import re
import boto3
import validators
import mysql.connector
import jwt
import socket  # DEBUG TODO: REMOVE.
from urllib.parse import urlparse
from botocore.config import Config
from boto3.exceptions import Boto3Error
from botocore.exceptions import (
    ClientError,
    BotoCoreError,
    NoCredentialsError,
    PartialCredentialsError,
)
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from requests import RequestException
from typing import Any, Dict
from boto3.exceptions import Boto3Error

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
        raise ValidationError(f"Invalid URL or domain name: '{url}'")

    # Remove www. if present (normalize the hostname)
    hostname = hostname.lstrip("www.")

    # Validate the domain using a regex (ensure it has at least one dot)
    if not re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", hostname):
        raise ValidationError(f"Invalid domain name: '{hostname}'")

    # Extract the full domain (e.g., blog.example.com)
    full_domain = hostname

    # Extract the root domain (e.g., 'example' from blog.example.com)
    domain_parts = full_domain.split(".")
    if len(domain_parts) >= 2:
        root_domain = domain_parts[-2]
    else:
        raise ValidationError(f"Unable to extract root domain from: '{full_domain}'")

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


def get_secret(secret_name: str) -> str:
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
        ValidationError: (400, lambda e: f"Invalid input: {e.message}"),
        json.JSONDecodeError: (400, lambda e: "Invalid JSON format"),
        ValueError: (400, lambda e: str(e)),
        RequestException: (502, lambda e: "Bad Gateway"),
        KeyError: (400, lambda e: f"Key error: {e.args[0]}"),
        Boto3Error: (500, lambda e: "An unspecified error occurred"),
        BotoCoreError: (500, lambda e: "An unspecified error occurred"),
        NoCredentialsError: (500, lambda e: "No AWS credentials found"),
        PartialCredentialsError: (500, lambda e: "Partial AWS credentials found"),
        ClientError: (500, lambda e: e.response["Error"]["Message"]),
        jwt.ExpiredSignatureError: (401, lambda e: "Token has expired"),
        jwt.InvalidTokenError: (401, lambda e: "Invalid token"),
    }
    clients = get_aws_clients()
    for client_name, client in clients.items():
        client_exceptions = {
            getattr(client.exceptions, exception_name): (
                500,
                lambda error_message: f"{exception_name}: {str(error_message)}",
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
                "body": json.dumps({"error": message_func(e)}),
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


def process_input(body: Dict[str, Any], schemapath: str) -> Dict[str, Any]:
    schema = load_schema(schemapath)
    output = {}
    try:
        validate(body, schema)

        if "contact_id" in body:
            if not str(body["contact_id"]).isdigit():
                raise ValidationError("contact_id must only contain numbers")
            output["contact_id"] = body["contact_id"]

        if "appname" in body:
            if not body["appname"].isalnum() or len(body["appname"]) > 14:
                raise ValidationError("invalid appname")
            output["appname"] = body["appname"]

        if "vanity_name" in body:
            full_domain, root_domain = extract_domain(body["vanity_name"])
            if not validators.domain(full_domain):
                raise ValidationError("vanity_name must be a valid domain")
            output["vanity_name"] = full_domain
            output["org_name"] = root_domain

        if "email_username" in body:
            email_address = f"{body['email_username']}@{output['vanity_name']}"
            if not validators.email(email_address):
                raise ValidationError("email_username must be a valid email username")
            output["email_username"] = body["email_username"]
            output["email_address"] = email_address

    except ValidationError as e:
        raise e

    return output
