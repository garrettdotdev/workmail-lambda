import unittest
from unittest.mock import patch, MagicMock
import os
import json
from check_domain_verification_function.app import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @patch("check_domain_verification_function.app.get_aws_client")
    @patch("check_domain_verification_function.app.validate")
    @patch("check_domain_verification_function.app.handle_error")
    def test_lambda_handler_success(
        self, mock_handle_error, mock_validate, mock_get_aws_client
    ):
        # Mocking the validate function to return True
        mock_validate.return_value = True

        # Mocking the WorkMail client
        mock_workmail_client = MagicMock()
        mock_workmail_client.describe_mail_domain.return_value = {
            "OwnershipVerificationStatus": "VERIFIED",
            "DkimVerificationStatus": "VERIFIED",
        }
        mock_get_aws_client.return_value = mock_workmail_client

        event = {"organization_id": "org-123", "vanity_name": "example.com"}
        context = {}

        response = lambda_handler(event, context)
        self.assertEqual(response, {"domainVerification": True})

    @patch("check_domain_verification_function.app.get_aws_client")
    @patch("check_domain_verification_function.app.validate")
    @patch("check_domain_verification_function.app.handle_error")
    def test_lambda_handler_validation_failure(
        self, mock_handle_error, mock_validate, mock_get_aws_client
    ):
        # Mocking the validate function to return False
        mock_validate.return_value = False

        event = {"organization_id": "org-123", "vanity_name": "example.com"}
        context = {}

        lambda_handler(event, context)
        mock_handle_error.assert_called_once()
        self.assertTrue(
            "Input validation failed" in str(mock_handle_error.call_args[0][0])
        )

    @patch("check_domain_verification_function.app.get_aws_client")
    @patch("check_domain_verification_function.app.validate")
    @patch("check_domain_verification_function.app.handle_error")
    def test_lambda_handler_unexpected_response(
        self, mock_handle_error, mock_validate, mock_get_aws_client
    ):
        # Mocking the validate function to return True
        mock_validate.return_value = True

        # Mocking the WorkMail client with an unexpected response
        mock_workmail_client = MagicMock()
        mock_workmail_client.describe_mail_domain.return_value = {
            "UnexpectedKey": "UnexpectedValue"
        }
        mock_get_aws_client.return_value = mock_workmail_client

        event = {"organization_id": "org-123", "vanity_name": "example.com"}
        context = {}

        lambda_handler(event, context)
        mock_handle_error.assert_called_once()
        self.assertTrue(
            "Unexpected response from WorkMail"
            in str(mock_handle_error.call_args[0][0])
        )

    @patch("check_domain_verification_function.app.get_aws_client")
    @patch("check_domain_verification_function.app.validate")
    @patch("check_domain_verification_function.app.handle_error")
    def test_lambda_handler_verification_failure(
        self, mock_handle_error, mock_validate, mock_get_aws_client
    ):
        # Mocking the validate function to return True
        mock_validate.return_value = True

        # Mocking the WorkMail client with a verification failure response
        mock_workmail_client = MagicMock()
        mock_workmail_client.describe_mail_domain.return_value = {
            "OwnershipVerificationStatus": "PENDING",
            "DkimVerificationStatus": "PENDING",
        }
        mock_get_aws_client.return_value = mock_workmail_client

        event = {"organization_id": "org-123", "vanity_name": "example.com"}
        context = {}

        response = lambda_handler(event, context)
        self.assertEqual(response, {"domainVerification": False})


if __name__ == "__main__":
    unittest.main()