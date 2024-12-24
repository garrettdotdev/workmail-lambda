# start_create_workmail_workflow_function/app.py
import json
import logging
from start_create_workmail_workflow_function.config import get_config
from typing import Dict, Any
from workmail_common.utils import (
    get_aws_client,
    handle_error,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
