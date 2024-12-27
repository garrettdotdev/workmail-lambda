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
    process_input,
    connect_to_rds,
    get_aws_clients,
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
        sql = """
        SELECT organization_id
        FROM workmail_organizations
        WHERE ownerid = %s
        AND vanity_name = %s
        LIMIT 1
        """
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


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        config = get_config()
        aws_clients = get_aws_clients(region_name="us-east-1")

        body = json.loads(event["body"])

        pwd = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(pwd, "/schemas/input_schema.json")
        clean_input = process_input(body, schema_path)

        contact_id = clean_input["contact_id"]
        vanity_name = clean_input["vanity_name"]

        organization_id = get_workmail_organization_id(
            contact_id, vanity_name, aws_clients["rds_client"], config=config
        )
        delete_workmail_organization_response = delete_workmail_organization(
            organization_id, aws_clients["cloudformation_client"]
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
