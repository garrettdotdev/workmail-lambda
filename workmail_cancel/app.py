import json
import os
import jsonschema
from jsonschema import validate
import boto3
import logging
from botocore.exceptions import ClientError, BotoCoreError
from typing import Dict, Any
from workmail_cancel.config import get_config
from workmail_common.utils import load_schema, handle_error

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_aws_clients(region_name: str) -> Dict[str, Any]:
    return {
        "rds_client": boto3.client("rds-data", region_name=region_name),
        "cloudformation_client": boto3.client(
            "cloudformation", region_name=region_name
        ),
    }


def query_workmail_stack(
    contact_id: int, appname: str, rds_client: Any, config: Dict[str, str]
) -> str:
    try:
        db_secret_arn = config["DB_SECRET_ARN"]
        db_cluster_arn = config["DB_CLUSTER_ARN"]
        database_name = config["DATABASE_NAME"]
        sql = """
        SELECT stackid
        FROM workmail_stacks
        WHERE ownerid = :contact_id
        LIMIT 1
        """
        response = rds_client.execute_statement(
            secretArn=db_secret_arn,
            resourceArn=db_cluster_arn,
            sql=sql,
            database=database_name,
            parameters=[
                {"name": "contact_id", "value": {"longValue": contact_id}},
                {"name": "appname", "value": {"stringValue": appname}},
            ],
        )
        if not response["records"]:
            raise ValueError(
                f"No WorkMail stack found with contact_id={contact_id} and appname={appname}"
            )
        stack_id = response["records"][0][0]["stringValue"]
        logger.info(f"Found WorkMail stack with stack_id={stack_id}")
        return stack_id
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to query RDS: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying RDS: {e}")
        raise


def delete_workmail_stack(stack_id: str, cloudformation_client: Any) -> None:
    try:
        cloudformation_client.delete_stack(StackName=stack_id)
        logger.info(f"Initiated deletion of WorkMail stack with stack_id={stack_id}")
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to delete WorkMail stack: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting WorkMail stack: {e}")
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        config = get_config()
        aws_clients = get_aws_clients(region_name="us-east-1")

        pwd = os.path.dirname(os.path.abspath(__file__))
        schema_path = f"{pwd}/schemas/input_schema.json"
        input_schema = load_schema(schema_path)

        body = json.loads(event["body"])
        validate(instance=body, schema=input_schema)

        contact_id = body["contact_id"]
        appname = body["appname"]
        vanity_name = body["vanity_name"]

        stack_id = query_workmail_stack(
            contact_id, appname, aws_clients["rds_client"], config=config
        )
        delete_workmail_stack(stack_id, aws_clients["cloudformation_client"])

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "WorkMail stack deletion initiated.", "stackId": stack_id}
            ),
        }
    except Exception as e:
        return handle_error(e)
