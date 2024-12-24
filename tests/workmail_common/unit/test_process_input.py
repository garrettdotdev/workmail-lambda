import unittest
from unittest.mock import patch, MagicMock
from workmail_common.utils import process_input, extract_domain, validate


class TestProcessInput(unittest.TestCase):

    @patch("workmail_common.utils.validate")
    @patch("workmail_common.utils.extract_domain")
    def test_process_input_valid(self, mock_extract_domain, mock_validate):
        # Mocking the validation and domain extraction
        mock_validate.return_value = True
        mock_extract_domain.return_value = ("example.com", "example")

        # Valid input
        body = {
            "vanity_name": "example.com",
            "email_username": "user",
        }
        schema_path = "path/to/schema.json"

        # Expected output
        expected_output = {
            "vanity_name": "example.com",
            "organization_name": "example",
            "email_username": "user",
            "email_address": "user@example.com",
        }

        # Calling the function
        result = process_input(body, schema_path)

        # Assertions
        self.assertEqual(result, expected_output)
        mock_validate.assert_called_once_with(body, schema_path)
        mock_extract_domain.assert_called_once_with("example.com")

    @patch("workmail_common.utils.validate")
    @patch("workmail_common.utils.extract_domain")
    def test_process_input_invalid_domain(self, mock_extract_domain, mock_validate):
        # Mocking the validation and domain extraction
        mock_validate.return_value = True
        mock_extract_domain.side_effect = Exception("Invalid domain name")

        # Invalid input
        body = {
            "vanity_name": "invalid_domain",
            "email_username": "user",
        }
        schema_path = "path/to/schema.json"

        # Calling the function and asserting exception
        with self.assertRaises(Exception) as context:
            process_input(body, schema_path)

        self.assertIn("Invalid domain name", str(context.exception))
        mock_validate.assert_called_once_with(body, schema_path)
        mock_extract_domain.assert_called_once_with("invalid_domain")

    @patch("workmail_common.utils.validate")
    @patch("workmail_common.utils.extract_domain")
    def test_process_input_validation_failure(self, mock_extract_domain, mock_validate):
        # Mocking the validation and domain extraction
        mock_validate.side_effect = Exception("Schema validation error")
        mock_extract_domain.return_value = ("example.com", "example")

        # Invalid input
        body = {
            "vanity_name": "example.com",
            "email_username": "user",
        }
        schema_path = "path/to/schema.json"

        # Calling the function and asserting exception
        with self.assertRaises(Exception) as context:
            process_input(body, schema_path)

        self.assertIn("Schema validation error", str(context.exception))
        mock_validate.assert_called_once_with(body, schema_path)
        mock_extract_domain.assert_not_called()

    @patch("workmail_common.utils.validate")
    @patch("workmail_common.utils.extract_domain")
    def test_process_input_missing_email_username(
        self, mock_extract_domain, mock_validate
    ):
        # Mocking the validation and domain extraction
        mock_validate.return_value = True
        mock_extract_domain.return_value = ("example.com", "example")

        # Invalid input
        body = {
            "vanity_name": "example.com",
        }
        schema_path = "path/to/schema.json"

        # Calling the function and asserting exception
        with self.assertRaises(KeyError) as context:
            process_input(body, schema_path)

        self.assertIn("email_username", str(context.exception))
        mock_validate.assert_called_once_with(body, schema_path)
        mock_extract_domain.assert_called_once_with("example.com")


if __name__ == "__main__":
    unittest.main()
