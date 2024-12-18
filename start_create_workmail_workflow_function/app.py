import json
import logging
import os
import boto3
import botocore
from typing import Dict, Any, List, Tuple
from workmail_common.utils import (
    get_aws_client,
    handle_error,
)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:

    state_machine_arn = os.getenv("WORKMAIL_STEPFUNCTION_ARN")
    if not state_machine_arn:
        raise ValueError("WORKMAIL_STEPFUNCTION_ARN must be set")

    stepfunctions_client = get_aws_client("stepfunctions")

    try:
        response = stepfunctions_client.start_execution(
            stateMachineArn=state_machine_arn,
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
