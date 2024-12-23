import unittest
from unittest.mock import patch, MagicMock
from workmail_common.utils import process_input, load_schema, validate, extract_domain


class TestProcessInput(unittest.TestCase):

    @patch("workmail_common.utils.load_schema")
    @patch("workmail_common.utils.validate")
    @patch("workmail_common.utils.extract_domain")
    def test_process_input_success(
        self, mock_extract_domain, mock_validate, mock_load_schema
    ):
        # Mock the schema and domain extraction
        mock_load_schema.return_value = {
            "type": "object",
            "properties": {"vanity_name": {"type": "string"}},
        }
        mock_extract_domain.return_value = ("blog.example.com", "example")

        # Define a sample body
        body = {"vanity_name": "blog.example.com", "email_username": "user"}

        # Call the function
        result = process_input(body, "schema.json")

        # Assertions
        mock_load_schema.assert_called_once_with("schema.json")
        mock_validate.assert_called_once_with(body, mock_load_schema.return_value)
        mock_extract_domain.assert_called_once_with("blog.example.com")
        self.assertEqual(result["vanity_name"], "blog.example.com")
        self.assertEqual(result["org_name"], "example")
        self.assertEqual(result["email_address"], "user@blog.example.com")

    @patch("workmail_common.utils.load_schema")
    @patch("workmail_common.utils.validate")
    @patch("workmail_common.utils.extract_domain")
    def test_process_input_validation_error(
        self, mock_extract_domain, mock_validate, mock_load_schema
    ):
        # Mock the schema and validation to raise an exception
        mock_load_schema.return_value = {
            "type": "object",
            "properties": {"vanity_name": {"type": "string"}},
        }
        mock_validate.side_effect = Exception("Validation error")

        # Define a sample body
        body = {"vanity_name": "blog.example.com", "email_username": "user"}

        # Call the function and assert it raises an exception
        with self.assertRaises(Exception) as context:
            process_input(body, "schema.json")

        self.assertEqual(str(context.exception), "Validation error")
        mock_load_schema.assert_called_once_with("schema.json")
        mock_validate.assert_called_once_with(body, mock_load_schema.return_value)
        mock_extract_domain.assert_not_called()

    @patch("workmail_common.utils.load_schema")
    @patch("workmail_common.utils.validate")
    @patch("workmail_common.utils.extract_domain")
    def test_process_input_extract_domain_error(
        self, mock_extract_domain, mock_validate, mock_load_schema
    ):
        # Mock the schema and domain extraction to raise an exception
        mock_load_schema.return_value = {
            "type": "object",
            "properties": {"vanity_name": {"type": "string"}},
        }
        mock_extract_domain.side_effect = Exception("Domain extraction error")

        # Define a sample body
        body = {"vanity_name": "invalid_domain", "email_username": "user"}

        # Call the function and assert it raises an exception
        with self.assertRaises(Exception) as context:
            process_input(body, "schema.json")

        self.assertEqual(str(context.exception), "Domain extraction error")
        mock_load_schema.assert_called_once_with("schema.json")
        mock_validate.assert_called_once_with(body, mock_load_schema.return_value)
        mock_extract_domain.assert_called_once_with("invalid_domain")


if __name__ == "__main__":
    unittest.main()
