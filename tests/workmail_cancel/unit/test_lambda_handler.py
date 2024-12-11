import unittest
from unittest.mock import patch, MagicMock
from workmail_cancel.app import lambda_handler, load_schema
from jsonschema.exceptions import ValidationError
from json import JSONDecodeError
from botocore.exceptions import ClientError, BotoCoreError
import json


class TestLambdaHandler(unittest.TestCase):
    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.get_aws_clients")
    @patch("workmail_cancel.app.validate")
    @patch("workmail_cancel.app.query_workmail_stack")
    @patch("workmail_cancel.app.delete_workmail_stack")
    def test_lambda_handler_success(
        self,
        mock_delete_workmail_stack,
        mock_query_workmail_stack,
        mock_validate,
        mock_get_aws_clients,
        mock_get_config,
    ):
        # Arrange
        event = {
            "body": json.dumps(
                {"contact_id": 1, "appname": "myapp", "vanity_name": "myvanity"}
            )
        }
        context = {}
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:mysecret",
            "DB_CLUSTER_ARN": "arn:aws:rds:us-east-1:123456789012:cluster:mycluster",
            "DATABASE_NAME": "mydatabase",
        }
        mock_get_aws_clients.return_value = {
            "rds_client": MagicMock(),
            "cloudformation_client": MagicMock(),
        }
        mock_query_workmail_stack.return_value = "stack123"

        # Act
        response = lambda_handler(event, context)

        # Assert
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("WorkMail stack deletion initiated.", response["body"])
        self.assertIn("stack123", response["body"])
        mock_query_workmail_stack.assert_called_once()
        mock_delete_workmail_stack.assert_called_once()

    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.get_aws_clients")
    @patch("workmail_cancel.app.validate")
    def test_lambda_handler_validation_error(
        self,
        mock_validate,
        mock_get_aws_clients,
        mock_get_config,
    ):
        # Arrange
        event = {"body": json.dumps({"contact_id": 1, "appname": "myapp"})}
        context = {}
        mock_validate.side_effect = ValidationError("Invalid input")

        # Act
        response = lambda_handler(event, context)

        # Assert
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid input", response["body"])

    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.get_aws_clients")
    def test_lambda_handler_json_decode_error(
        self,
        mock_get_aws_clients,
        mock_get_config,
    ):
        # Arrange
        event = {"body": "invalid json"}
        context = {}

        # Act
        response = lambda_handler(event, context)

        # Assert
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid JSON format", response["body"])

    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.get_aws_clients")
    @patch("workmail_cancel.app.validate")
    @patch("workmail_cancel.app.query_workmail_stack")
    @patch("workmail_cancel.app.delete_workmail_stack")
    def test_lambda_handler_unexpected_error(
        self,
        mock_delete_workmail_stack,
        mock_query_workmail_stack,
        mock_validate,
        mock_get_aws_clients,
        mock_get_config,
    ):
        # Arrange
        event = {
            "body": json.dumps(
                {"contact_id": 1, "appname": "myapp", "vanity_name": "myvanity"}
            )
        }
        context = {}
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:mysecret",
            "DB_CLUSTER_ARN": "arn:aws:rds:us-east-1:123456789012:cluster:mycluster",
            "DATABASE_NAME": "mydatabase",
        }
        mock_get_aws_clients.return_value = {
            "rds_client": MagicMock(),
            "cloudformation_client": MagicMock(),
        }
        mock_query_workmail_stack.side_effect = Exception("Unexpected error")

        # Act
        response = lambda_handler(event, context)

        # Assert
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Unexpected error", response["body"])


if __name__ == "__main__":
    unittest.main()
