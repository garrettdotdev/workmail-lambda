import unittest
from unittest.mock import patch, MagicMock
from workmail_common.utils import handle_error
from botocore.exceptions import (
    BotoCoreError,
    NoCredentialsError,
    ClientError,
    PartialCredentialsError,
)
import json
from requests import RequestException


class TestHandleError(unittest.TestCase):

    def test_handle_error_json_decode_error(self):
        error = json.JSONDecodeError("Expecting value", "doc", 0)
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid JSON format", response["errorMessage"])

    def test_handle_error_value_error(self):
        error = ValueError("Invalid value")
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid value", response["errorMessage"])

    def test_handle_error_request_exception(self):
        error = RequestException("Bad Gateway")
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 502)
        self.assertIn("Bad Gateway", response["errorMessage"])

    def test_handle_error_key_error(self):
        error = KeyError("missing_key")
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Key error: missing_key", response["errorMessage"])

    def test_handle_error_boto3_error(self):
        error = BotoCoreError()
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("An unspecified error occurred", response["errorMessage"])

    def test_handle_error_no_credentials_error(self):
        error = NoCredentialsError()
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("No AWS credentials found", response["errorMessage"])

    def test_handle_error_partial_credentials_error(self):
        error = PartialCredentialsError(
            provider="aws", cred_var="AWS_SECRET_ACCESS_KEY"
        )
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Partial AWS credentials found", response["errorMessage"])

    def test_handle_error_client_error(self):
        error = ClientError(
            error_response={
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Secret not found",
                }
            },
            operation_name="GetSecretValue",
        )
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Secret not found", response["errorMessage"])

    @patch("workmail_common.utils.get_aws_clients")
    def test_handle_error_custom_client_exception(self, mock_get_aws_clients):
        mock_client = MagicMock()
        mock_client.exceptions.CustomException = type(
            "CustomException", (Exception,), {}
        )
        mock_get_aws_clients.return_value = {"mock_client": mock_client}

        error = mock_client.exceptions.CustomException("Custom error")
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("CustomException: Custom error", response["errorMessage"])

    def test_handle_error_unexpected_error(self):
        error = Exception("Unexpected error")
        response = handle_error(error)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Unexpected error", response["errorMessage"])


if __name__ == "__main__":
    unittest.main()
