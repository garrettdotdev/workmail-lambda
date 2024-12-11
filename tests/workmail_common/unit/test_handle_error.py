import unittest
from unittest.mock import MagicMock
from workmail_common.utils import handle_error
from jsonschema.exceptions import ValidationError
from json import JSONDecodeError
from botocore.exceptions import ClientError, BotoCoreError


class TestHandleError(unittest.TestCase):
    def test_handle_error_validation_error(self):
        # Arrange
        error = ValidationError("Invalid input")

        # Act
        response = handle_error(error)

        # Assert
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid input", response["body"])

    def test_handle_error_json_decode_error(self):
        # Arrange
        error = JSONDecodeError("Invalid JSON format", "", 0)

        # Act
        response = handle_error(error)

        # Assert
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid JSON format", response["body"])

    def test_handle_error_client_error(self):
        # Arrange
        error = ClientError(
            {"Error": {"Code": "ClientError", "Message": "An error occurred"}},
            "operation",
        )

        # Act
        response = handle_error(error)

        # Assert
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("An error occurred", response["body"])

    def test_handle_error_boto_core_error(self):
        # Arrange
        error = BotoCoreError()

        # Act
        response = handle_error(error)

        # Assert
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("An unspecified error occurred", response["body"])

    def test_handle_error_value_error(self):
        # Arrange
        error = ValueError("Value error occurred")

        # Act
        response = handle_error(error)

        # Assert
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Value error occurred", response["body"])

    def test_handle_error_unexpected_error(self):
        # Arrange
        error = Exception("Unexpected error occurred")

        # Act
        response = handle_error(error)

        # Assert
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Unexpected error occurred", response["body"])


if __name__ == "__main__":
    unittest.main()
