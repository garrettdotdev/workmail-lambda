import unittest
import json
from unittest.mock import patch, MagicMock
from start_create_workmail_workflow_function.app import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @patch("start_create_workmail_workflow_function.app.get_config")
    @patch("start_create_workmail_workflow_function.app.get_aws_client")
    def test_lambda_handler_success(self, mock_get_aws_client, mock_get_config):
        # Mock the configuration
        mock_get_config.return_value = {
            "WORKMAIL_STEPFUNCTION_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:exampleStateMachine"
        }

        # Mock the Step Functions client
        mock_sfn_client = MagicMock()
        mock_sfn_client.start_execution.return_value = {
            "executionArn": "arn:aws:states:us-east-1:123456789012:execution:exampleStateMachine:exampleExecution"
        }
        mock_get_aws_client.return_value = mock_sfn_client

        # Define a sample event
        event = {"key1": "value1", "key2": "value2"}

        # Call the lambda_handler function
        response = lambda_handler(event, None)

        # Assert the response
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("WorkMail creation workflow started", response["body"])
        self.assertIn("executionArn", response["body"])

        # Assert the start_execution call
        mock_sfn_client.start_execution.assert_called_once_with(
            stateMachineArn="arn:aws:states:us-east-1:123456789012:stateMachine:exampleStateMachine",
            name="create_workmail_workflow",
            input=json.dumps(event),
        )

    @patch("start_create_workmail_workflow_function.app.get_config")
    @patch("start_create_workmail_workflow_function.app.get_aws_client")
    @patch("start_create_workmail_workflow_function.app.handle_error")
    def test_lambda_handler_exception(
        self, mock_handle_error, mock_get_aws_client, mock_get_config
    ):
        # Mock the configuration
        mock_get_config.return_value = {
            "WORKMAIL_STEPFUNCTION_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:exampleStateMachine"
        }

        # Mock the Step Functions client to raise an exception
        mock_sfn_client = MagicMock()
        mock_sfn_client.start_execution.side_effect = Exception("Test exception")
        mock_get_aws_client.return_value = mock_sfn_client

        # Define a sample event
        event = {"key1": "value1", "key2": "value2"}

        # Call the lambda_handler function
        lambda_handler(event, None)

        # Assert the handle_error call
        mock_handle_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
