import unittest
from unittest.mock import patch, MagicMock
import json
from workmail_cancel.app import lambda_handler, load_schema
from botocore.exceptions import ClientError, BotoCoreError


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
        # Mock configurations
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
            "DB_CLUSTER_ARN": "arn:aws:rds:region:account-id:cluster:cluster-id",
            "DATABASE_NAME": "database_name",
        }

        # Mock AWS clients
        mock_get_aws_clients.return_value = {
            "rds_client": MagicMock(),
            "cloudformation_client": MagicMock(),
        }

        # Mock query_workmail_stack
        mock_query_workmail_stack.return_value = "mock_stack_id"

        # Mock event and context
        event = {
            "body": json.dumps(
                {"contact_id": 123, "appname": "test_app", "vanity_name": "example.com"}
            )
        }
        context = {}

        # Call the lambda handler
        response = lambda_handler(event, context)

        # Assertions
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("WorkMail stack deletion initiated.", response["body"])
        self.assertIn("mock_stack_id", response["body"])

        # Ensure the helper functions were called
        mock_get_config.assert_called_once()
        mock_get_aws_clients.assert_called_once_with(region_name="us-east-1")
        mock_validate.assert_called_once()
        mock_query_workmail_stack.assert_called_once_with(
            123,
            "test_app",
            mock_get_aws_clients.return_value["rds_client"],
            config=mock_get_config.return_value,
        )
        mock_delete_workmail_stack.assert_called_once_with(
            "mock_stack_id", mock_get_aws_clients.return_value["cloudformation_client"]
        )

    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.get_aws_clients")
    @patch("workmail_cancel.app.query_workmail_stack")
    @patch("workmail_cancel.app.delete_workmail_stack")
    def test_lambda_handler_invalid_input(
        self,
        mock_delete_workmail_stack,
        mock_query_workmail_stack,
        mock_get_aws_clients,
        mock_get_config,
    ):
        # Mock configurations
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
            "DB_CLUSTER_ARN": "arn:aws:rds:region:account-id:cluster:cluster-id",
            "DATABASE_NAME": "database_name",
        }

        # Mock AWS clients
        mock_get_aws_clients.return_value = {
            "rds_client": MagicMock(),
            "cloudformation_client": MagicMock(),
        }

        # Mock event with invalid input
        event = {
            "body": json.dumps(
                {
                    "contact_id": "invalid_id",
                    "appname": "test_app",
                    "vanity_name": "example.com",
                }
            )
        }
        context = {}

        # Call the lambda handler
        response = lambda_handler(event, context)

        # Assertions
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid input", response["body"])

    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.get_aws_clients")
    @patch("workmail_cancel.app.validate")
    @patch("workmail_cancel.app.query_workmail_stack")
    @patch("workmail_cancel.app.delete_workmail_stack")
    def test_lambda_handler_aws_client_error(
        self,
        mock_delete_workmail_stack,
        mock_query_workmail_stack,
        mock_validate,
        mock_get_aws_clients,
        mock_get_config,
    ):
        # Mock configurations
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
            "DB_CLUSTER_ARN": "arn:aws:rds:region:account-id:cluster:cluster-id",
            "DATABASE_NAME": "database_name",
        }

        # Mock AWS clients
        mock_get_aws_clients.return_value = {
            "rds_client": MagicMock(),
            "cloudformation_client": MagicMock(),
        }

        # Mock query_workmail_stack to raise ClientError
        mock_query_workmail_stack.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Server Error"}}, "Query"
        )

        # Mock event and context
        event = {
            "body": json.dumps(
                {"contact_id": 123, "appname": "test_app", "vanity_name": "example.com"}
            )
        }
        context = {}

        # Call the lambda handler
        response = lambda_handler(event, context)

        # Assertions
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Internal Server Error", response["body"])

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
        # Mock configurations
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
            "DB_CLUSTER_ARN": "arn:aws:rds:region:account-id:cluster:cluster-id",
            "DATABASE_NAME": "database_name",
        }

        # Mock AWS clients
        mock_get_aws_clients.return_value = {
            "rds_client": MagicMock(),
            "cloudformation_client": MagicMock(),
        }

        # Mock query_workmail_stack to raise an unexpected error
        mock_query_workmail_stack.side_effect = Exception("Unexpected error")

        # Mock event and context
        event = {
            "body": json.dumps(
                {"contact_id": 123, "appname": "test_app", "vanity_name": "example.com"}
            )
        }
        context = {}

        # Call the lambda handler
        response = lambda_handler(event, context)

        # Assertions
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Unexpected error", response["body"])


if __name__ == "__main__":
    unittest.main()
