# tests/create_workmail_org_function/unit/test_lambda_handler.py
import unittest
import json
from unittest.mock import patch, MagicMock
from create_workmail_org_function.app import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @patch("create_workmail_org_function.app.keap_contact_add_to_group_via_proxy")
    @patch("create_workmail_org_function.app.keap_contact_create_note_via_proxy")
    @patch("create_workmail_org_function.app.prepare_keap_updates")
    @patch("create_workmail_org_function.app.get_dns_records")
    @patch("create_workmail_org_function.app.register_workmail_organization")
    @patch("create_workmail_org_function.app.create_workmail_org")
    @patch("create_workmail_org_function.app.get_client_info")
    @patch("create_workmail_org_function.app.process_input")
    @patch("create_workmail_org_function.app.connect_to_rds")
    @patch("create_workmail_org_function.app.get_aws_clients")
    @patch("create_workmail_org_function.app.get_config")
    def test_lambda_handler_success(
        self,
        mock_get_config,
        mock_get_aws_clients,
        mock_connect_to_rds,
        mock_process_input,
        mock_get_client_info,
        mock_create_workmail_org,
        mock_register_workmail_organization,
        mock_get_dns_records,
        mock_prepare_keap_updates,
        mock_keap_contact_create_note_via_proxy,
        mock_keap_contact_add_to_group_via_proxy,
    ):
        # Arrange
        event = {
            "body": json.dumps(
                {
                    "contact_id": 1,
                    "appname": "test-app",
                    "vanity_name": "test-vanity",
                    "organization_name": "test-org",
                    "email_username": "testuser",
                    "email_address": "testuser@example.com",
                }
            )
        }
        context = {}
        mock_get_config.return_value = {"KEAP_TAG": 123}
        mock_get_aws_clients.return_value = {
            "workmail_client": MagicMock(),
            "secretsmanager_client": MagicMock(),
        }
        mock_connect_to_rds.return_value = MagicMock()
        mock_process_input.return_value = json.loads(event["body"])
        mock_get_client_info.return_value = ("John", "Doe")
        mock_create_workmail_org.return_value = {"organization_id": "test-org-id"}
        mock_get_dns_records.return_value = [
            {"Hostname": "test1._amazonses.example.com", "Value": "value1"},
            {"Hostname": "test2._domainkey.example.com", "Value": "value2"},
        ]
        mock_prepare_keap_updates.return_value = {
            "API1": "value1",
            "API2": "value2",
        }

        # Act
        result = lambda_handler(event, context)

        # Assert
        self.assertEqual(result["contact_id"], 1)
        self.assertEqual(result["organization_id"], "test-org-id")
        self.assertEqual(result["organization_name"], "test-org")
        self.assertEqual(result["email_username"], "testuser")
        self.assertEqual(result["vanity_name"], "test-vanity")
        self.assertEqual(result["email_address"], "testuser@example.com")
        self.assertEqual(result["first_name"], "John")
        self.assertEqual(result["last_name"], "Doe")

    @patch("create_workmail_org_function.app.keap_contact_add_to_group_via_proxy")
    @patch("create_workmail_org_function.app.keap_contact_create_note_via_proxy")
    @patch("create_workmail_org_function.app.prepare_keap_updates")
    @patch("create_workmail_org_function.app.get_dns_records")
    @patch("create_workmail_org_function.app.register_workmail_organization")
    @patch("create_workmail_org_function.app.create_workmail_org")
    @patch("create_workmail_org_function.app.get_client_info")
    @patch("create_workmail_org_function.app.process_input")
    @patch("create_workmail_org_function.app.connect_to_rds")
    @patch("create_workmail_org_function.app.get_aws_clients")
    @patch("create_workmail_org_function.app.get_config")
    def test_lambda_handler_exception(
        self,
        mock_get_config,
        mock_get_aws_clients,
        mock_connect_to_rds,
        mock_process_input,
        mock_get_client_info,
        mock_create_workmail_org,
        mock_register_workmail_organization,
        mock_get_dns_records,
        mock_prepare_keap_updates,
        mock_keap_contact_create_note_via_proxy,
        mock_keap_contact_add_to_group_via_proxy,
    ):
        # Arrange
        event = {
            "body": json.dumps(
                {
                    "contact_id": 1,
                    "appname": "test-app",
                    "vanity_name": "test-vanity",
                    "organization_name": "test-org",
                    "email_username": "testuser",
                    "email_address": "testuser@example.com",
                }
            )
        }
        context = {}
        mock_get_config.return_value = {"KEAP_TAG": 123}
        mock_get_aws_clients.return_value = {
            "workmail_client": MagicMock(),
            "secretsmanager_client": MagicMock(),
        }
        mock_connect_to_rds.return_value = MagicMock()
        exception = Exception("Test exception")
        mock_process_input.side_effect = exception

        # Act & Assert
        with self.assertRaises(Exception) as context_manager:
            lambda_handler(event, context)

        self.assertEqual(str(context_manager.exception), "Test exception")


if __name__ == "__main__":
    unittest.main()
