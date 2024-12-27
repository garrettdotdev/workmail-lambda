# start_create_workmail_workflow_function/app.py
import json
import logging
import os
from typing import Dict, Any
from workmail_common.utils import (
    get_aws_client,
    handle_error,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_config():
    required_vars = ["WORKMAIL_STEPFUNCTION_ARN"]
    config = {}
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentError(
                f"Environment variable {var} is required but not set."
            )
        config[var] = value
    return config


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:

    logger.info(f"Received event: {event}")

    config = get_config()

    sfn_client = get_aws_client("stepfunctions")

    try:
        logger.info(f"Launching state machine")
        response = sfn_client.start_execution(
            stateMachineArn=config["WORKMAIL_STEPFUNCTION_ARN"],
            name="create_workmail_workflow",
            input=json.dumps(event),
        )
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "WorkMail creation workflow started",
                    "executionArn": response["executionArn"],
                }
            ),
        }
    except Exception as e:
        handle_error(e)
