# tests/start_create_workmail_workflow_function/unit/test_lambda_handler.py
import unittest
from unittest.mock import patch, MagicMock
import json
import os
from start_create_workmail_workflow_function.app import lambda_handler, get_config


class TestLambdaHandler(unittest.TestCase):

    @patch.dict(
        os.environ,
        {
            "WORKMAIL_STEPFUNCTION_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:exampleStateMachine"
        },
    )
    @patch("start_create_workmail_workflow_function.app.get_aws_client")
    @patch("start_create_workmail_workflow_function.app.socket.gethostbyname")
    def test_lambda_handler_success(self, mock_gethostbyname, mock_get_aws_client):
        # Arrange
        mock_gethostbyname.return_value = "127.0.0.1"
        mock_sfn_client = MagicMock()
        mock_sfn_client.meta.endpoint_url = "https://states.us-east-1.amazonaws.com"
        mock_sfn_client.start_execution.return_value = {
            "executionArn": "arn:aws:states:us-east-1:123456789012:execution:exampleStateMachine:exampleExecution"
        }
        mock_get_aws_client.return_value = mock_sfn_client

        event = {"key": "value"}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["message"], "WorkMail creation workflow started")
        self.assertEqual(
            body["executionArn"],
            "arn:aws:states:us-east-1:123456789012:execution:exampleStateMachine:exampleExecution",
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_lambda_handler_missing_env_var(self):
        # Arrange
        event = {"key": "value"}
        context = {}

        # Act & Assert
        with self.assertRaises(EnvironmentError):
            lambda_handler(event, context)

    @patch.dict(
        os.environ,
        {
            "WORKMAIL_STEPFUNCTION_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:exampleStateMachine"
        },
    )
    @patch("start_create_workmail_workflow_function.app.get_aws_client")
    @patch("start_create_workmail_workflow_function.app.socket.gethostbyname")
    @patch("start_create_workmail_workflow_function.app.handle_error")
    def test_lambda_handler_exception(
        self, mock_handle_error, mock_gethostbyname, mock_get_aws_client
    ):
        # Arrange
        exception = Exception("Test exception")
        mock_gethostbyname.return_value = "127.0.0.1"
        mock_sfn_client = MagicMock()
        mock_sfn_client.meta.endpoint_url = "https://states.us-east-1.amazonaws.com"
        mock_sfn_client.start_execution.side_effect = exception
        mock_get_aws_client.return_value = mock_sfn_client

        event = {"key": "value"}
        context = {}

        # Act
        lambda_handler(event, context)

        # Assert
        mock_handle_error.assert_called_once_with(exception)


if __name__ == "__main__":
    unittest.main()
