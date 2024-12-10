# test_app.py
import unittest
from unittest.mock import patch, MagicMock
import json
from workmail_create.app import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @patch("workmail_create.app.get_config")
    @patch("workmail_create.app.get_aws_clients")
    @patch("workmail_create.app.query_rds")
    @patch("workmail_create.app.create_workmail_stack")
    @patch("workmail_create.app.register_workmail_stack")
    @patch("workmail_create.app.set_ses_notifications")
    @patch("workmail_create.app.get_dns_records")
    @patch("workmail_create.app.update_contact")
    @patch("workmail_create.app.add_contact_to_group")
    def test_lambda_handler_success(
        self,
        mock_add_contact_to_group,
        mock_update_contact,
        mock_get_dns_records,
        mock_set_ses_notifications,
        mock_register_workmail_stack,
        mock_create_workmail_stack,
        mock_query_rds,
        mock_get_aws_clients,
        mock_get_config,
    ):
        # Mock configurations
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "mock_db_secret_arn",
            "DB_CLUSTER_ARN": "mock_db_cluster_arn",
            "DATABASE_NAME": "mock_database_name",
            "ORGANIZATION_ID": "mock_organization_id",
            "KEAP_BASE_URL": "https://api.infusionsoft.com/crm/rest/v1/",
            "KEAP_API_KEY": "mock_keap_api_key",
            "KEAP_TAG": 3153,
            "SNS_BOUNCE_ARN": "mock_sns_bounce_arn",
            "SNS_COMPLAINT_ARN": "mock_sns_complaint_arn",
            "SNS_DELIVERY_ARN": "mock_sns_delivery_arn",
        }

        # Mock AWS clients
        mock_get_aws_clients.return_value = {
            "rds_client": MagicMock(),
            "cloudformation_client": MagicMock(),
            "ses_client": MagicMock(),
            "workmail_client": MagicMock(),
        }

        # Mock RDS query response
        mock_query_rds.return_value = ("John", "Doe")

        # Mock create_workmail_stack response
        mock_create_workmail_stack.return_value = "mock_stack_id"

        # Mock get_dns_records response
        mock_get_dns_records.return_value = [
            {"Type": "CNAME", "Name": "mock_name", "Value": "mock_value"}
        ]

        # Mock event
        event = {
            "body": json.dumps(
                {
                    "contact_id": 123,
                    "appname": "mock_app",
                    "email_username": "johndoe",
                    "vanity_name": "example.com",
                }
            )
        }

        # Call the lambda_handler function
        response = lambda_handler(event, None)

        # Assert the response
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(
            body["message"], "WorkMail organization and user creation initiated."
        )
        self.assertEqual(body["stackId"], "mock_stack_id")
        self.assertEqual(body["email"], "johndoe@example.com")

        # Assert that the mocks were called
        mock_query_rds.assert_called_once()
        mock_create_workmail_stack.assert_called_once()
        mock_register_workmail_stack.assert_called_once()
        mock_set_ses_notifications.assert_called_once()
        mock_get_dns_records.assert_called_once()
        mock_update_contact.assert_called_once()
        mock_add_contact_to_group.assert_called_once()

    # Additional test for error handling
    @patch("workmail_create.app.get_config")
    @patch("workmail_create.app.get_aws_clients")
    @patch("workmail_create.app.query_rds")
    @patch("workmail_create.app.create_workmail_stack")
    @patch("workmail_create.app.register_workmail_stack")
    @patch("workmail_create.app.set_ses_notifications")
    @patch("workmail_create.app.get_dns_records")
    @patch("workmail_create.app.update_contact")
    @patch("workmail_create.app.add_contact_to_group")
    def test_lambda_handler_failure(
        self,
        mock_add_contact_to_group,
        mock_update_contact,
        mock_get_dns_records,
        mock_set_ses_notifications,
        mock_register_workmail_stack,
        mock_create_workmail_stack,
        mock_query_rds,
        mock_get_aws_clients,
        mock_get_config,
    ):
        # Mock configurations
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "mock_db_secret_arn",
            "DB_CLUSTER_ARN": "mock_db_cluster_arn",
            "DATABASE_NAME": "mock_database_name",
            "ORGANIZATION_ID": "mock_organization_id",
            "KEAP_BASE_URL": "https://api.infusionsoft.com/crm/rest/v1/",
            "KEAP_API_KEY": "mock_keap_api_key",
            "KEAP_TAG": 3153,
            "SNS_BOUNCE_ARN": "mock_sns_bounce_arn",
            "SNS_COMPLAINT_ARN": "mock_sns_complaint_arn",
            "SNS_DELIVERY_ARN": "mock_sns_delivery_arn",
        }

        # Mock AWS clients
        mock_get_aws_clients.return_value = {
            "rds_client": MagicMock(),
            "cloudformation_client": MagicMock(),
            "ses_client": MagicMock(),
            "workmail_client": MagicMock(),
        }

        # Mock RDS query to raise an exception
        mock_query_rds.side_effect = Exception("Internal server error")

        # Mock event
        event = {
            "body": json.dumps(
                {
                    "contact_id": 123,
                    "appname": "mock_app",
                    "email_username": "johndoe",
                    "vanity_name": "example.com",
                }
            )
        }

        # Call the lambda_handler function
        response = lambda_handler(event, None)

        # Assert the response
        self.assertEqual(response["statusCode"], 500)
        body = json.loads(response["body"])
        self.assertEqual(body["error"], "Internal server error")


if __name__ == "__main__":
    unittest.main()
