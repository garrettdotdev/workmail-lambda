import json
import os
import boto3
import logging
import uuid
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, Any
from workmail_common.utils import (
    handle_error,
    validate,
    connect_to_rds,
    get_aws_clients,
    keap_contact_add_to_group_via_proxy,
)

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_config():
    required_vars = [
        "DB_SECRET_ARN",
        "DB_CLUSTER_ARN",
        "DATABASE_NAME",
        "SNS_BOUNCE_ARN",
        "SNS_COMPLAINT_ARN",
        "SNS_DELIVERY_ARN",
        "KEAP_TAG_CANCEL",
        "KEAP_BASE_URL",
        "PROXY_ENDPOINT",
        "PROXY_ENDPOINT_HOST",
    ]
    config = {}
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentError(
                f"Environment variable {var} is required but not set."
            )
        config[var] = value
    return config


def get_workmail_organization_id(
    contact_id: int, vanity_name: str, connection: Any
) -> str:
    try:
        cursor = connection.cursor()
        sql = """SELECT organization_id FROM workmail_organizations WHERE ownerid = %s AND vanity_name = %s LIMIT 1"""
        cursor.execute(sql, (contact_id, vanity_name))
        result = cursor.fetchone()

        if not result:
            raise ValueError(
                f"No WorkMail organization_id found with contact_id={contact_id} and vanity_name={vanity_name}"
            )
        organization_id = result
        logger.info(f"Found WorkMail stack with stack_id={organization_id}")
        return organization_id
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to query RDS: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying RDS: {e}")
        raise
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()


def delete_workmail_organization(
    organization_id: str, workmail_client: Any
) -> Dict[str, Any]:
    try:
        logger.info(
            f"Deleting WorkMail organization with organization_id={organization_id}"
        )
        delete_organization_response = workmail_client.delete_organization(
            ClientToken=str(uuid.uuid4()),
            OrganizationId=organization_id,
            DeleteDirectory=True,
            ForceDelete=True,
        )
        logger.info(
            f"Delete response: {json.dumps(delete_organization_response, default=str)}"
        )
        return delete_organization_response
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to delete WorkMail organization: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting WorkMail organization: {e}")
        raise


def unregister_workmail_organization(organization_id, connection) -> bool:
    try:
        logger.info(f"Attempting to unregister WorkMail organization {organization_id}")
        cursor = connection.cursor()
        sql = """DELETE FROM workmail_organizations WHERE organization_id = %s"""
        cursor.execute(sql, (organization_id,))
        connection.commit()
        logger.info(f"Unregistered WorkMail organization {organization_id}")
        return True
    except Exception as e:
        return False
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda function handler."""
    logger.info("Handling Lambda event")
    try:
        config = get_config()
        aws_clients = get_aws_clients()

        connection = connect_to_rds(aws_clients["secretsmanager_client"], config=config)

        body = json.loads(event["body"])

        pwd = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(pwd, "schemas/input_schema.json")
        validate(body, schema_path)

        contact_id = body["contact_id"]
        vanity_name = body["vanity_name"]

        organization_id = get_workmail_organization_id(
            contact_id, vanity_name, connection
        )
        delete_workmail_organization_response = delete_workmail_organization(
            organization_id, aws_clients["workmail_client"]
        )
        keap_contact_add_to_group_via_proxy(
            contact_id, int(config["KEAP_TAG_CANCEL"]), config=config
        )
        if not unregister_workmail_organization(
            organization_id,
            connection,
        ):
            logger.error(
                f"Failed to unregister WorkMail organization {organization_id}. Please remove entry from workmail_organizations table."
            )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Deleted workmail organization.",
                    "organization_id": delete_workmail_organization_response[
                        "OrganizationId"
                    ],
                    "state": delete_workmail_organization_response["State"],
                }
            ),
        }
    except Exception as e:
        return handle_error(e)
