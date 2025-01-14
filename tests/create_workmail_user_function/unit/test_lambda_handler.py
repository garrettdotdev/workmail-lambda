# tests/create_workmail_user_function/unit/test_lambda_handler.py
import unittest
from unittest.mock import patch, MagicMock
from create_workmail_user_function.app import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @patch("create_workmail_user_function.app.get_config")
    @patch("create_workmail_user_function.app.validate")
    @patch("create_workmail_user_function.app.generate_random_password")
    @patch("create_workmail_user_function.app.get_aws_client")
    @patch("create_workmail_user_function.app.connect_to_rds")
    @patch("create_workmail_user_function.app.update_workmail_registration")
    @patch("create_workmail_user_function.app.keap_contact_create_note_via_proxy")
    def test_lambda_handler_success(
        self,
        mock_keap_contact_create_note_via_proxy,
        mock_update_workmail_registration,
        mock_connect_to_rds,
        mock_get_aws_client,
        mock_generate_random_password,
        mock_validate,
        mock_get_config,
    ):
        # Mocking the configuration
        mock_get_config.return_value = {
            "KEAP_BASE_URL": "https://api.example.com/",
            "KEAP_API_KEY_SECRET_NAME": "secret_name",
            "SNS_BOUNCE_ARN": "arn:aws:sns:region:account-id:bounce",
            "SNS_COMPLAINT_ARN": "arn:aws:sns:region:account-id:complaint",
            "SNS_DELIVERY_ARN": "arn:aws:sns:region:account-id:delivery",
            "KEAP_TAG": "12345",
        }

        # Mocking the validation
        mock_validate.return_value = True

        # Mocking the random password generation
        mock_generate_random_password.return_value = "RandomPassword123!"

        # Mocking the AWS clients
        mock_workmail_client = MagicMock()
        mock_secrets_manager_client = MagicMock()
        mock_get_aws_client.side_effect = lambda service_name: {
            "workmail": mock_workmail_client,
            "secretsmanager": mock_secrets_manager_client,
        }[service_name]

        # Mocking the create_user response
        mock_workmail_client.create_user.return_value = {"UserId": "user-id"}
        mock_workmail_client.register_to_work_mail.return_value = {}

        # Mocking the event and context
        event = {
            "contact_id": 1,
            "organization_id": "org-id",
            "organization_name": "example",
            "email_username": "user",
            "email_address": "user@example.com",
            "first_name": "First",
            "last_name": "Last",
        }
        context = {}

        # Calling the lambda_handler
        response = lambda_handler(event, context)

        # Assertions
        self.assertEqual(response, {"userCreated": True})
        mock_validate.assert_called_once()
        mock_generate_random_password.assert_called_once()
        mock_workmail_client.create_user.assert_called_once()
        mock_workmail_client.register_to_work_mail.assert_called_once()
        mock_keap_contact_create_note_via_proxy.assert_called_once()
        mock_update_workmail_registration.assert_called_once()

    @patch("create_workmail_user_function.app.get_config")
    @patch("create_workmail_user_function.app.validate")
    def test_lambda_handler_validation_failure(self, mock_validate, mock_get_config):
        # Mocking the configuration
        mock_get_config.return_value = {}

        # Mocking the validation to fail
        mock_validate.side_effect = Exception("Input validation failed")

        # Mocking the event and context
        event = {}
        context = {}

        # Calling the lambda_handler
        with self.assertRaises(Exception) as context_manager:
            lambda_handler(event, context)

        self.assertEqual(str(context_manager.exception), "Input validation failed")
        mock_validate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
