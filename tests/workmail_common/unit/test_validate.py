import unittest
import json
from unittest.mock import patch, mock_open
from workmail_common.utils import validate, load_schema
from fastjsonschema import JsonSchemaException


class TestValidate(unittest.TestCase):

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"type": "object", "properties": {"name": {"type": "string"}}}',
    )
    @patch("workmail_common.utils.json.load")
    def test_validate_valid_input(self, mock_json_load, mock_open):
        # Mocking the schema loading
        mock_json_load.return_value = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        # Valid input
        body = {"name": "example"}
        schema_path = "path/to/schema.json"

        # Calling the function
        result = validate(body, schema_path)

        # Assertions
        self.assertTrue(result)
        mock_open.assert_called_once_with(schema_path)
        mock_json_load.assert_called_once()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"type": "object", "properties": {"name": {"type": "string"}}}',
    )
    @patch("workmail_common.utils.json.load")
    def test_validate_invalid_input(self, mock_json_load, mock_open):
        # Mocking the schema loading
        mock_json_load.return_value = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        # Invalid input
        body = {"name": 123}
        schema_path = "path/to/schema.json"

        # Calling the function and asserting exception
        with self.assertRaises(JsonSchemaException):
            validate(body, schema_path)

        mock_open.assert_called_once_with(schema_path)
        mock_json_load.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("workmail_common.utils.json.load")
    def test_validate_schema_file_not_found(self, mock_json_load, mock_open):
        # Mocking the schema loading to raise FileNotFoundError
        mock_open.side_effect = FileNotFoundError

        # Input
        body = {"name": "example"}
        schema_path = "path/to/nonexistent_schema.json"

        # Calling the function and asserting exception
        with self.assertRaises(FileNotFoundError):
            validate(body, schema_path)

        mock_open.assert_called_once_with(schema_path)
        mock_json_load.assert_not_called()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"type": "object", "properties": {"name": {"type": "string"}}}',
    )
    @patch("workmail_common.utils.json.load")
    def test_validate_json_decode_error(self, mock_json_load, mock_open):
        # Mocking the schema loading to raise JSONDecodeError
        mock_json_load.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)

        # Input
        body = {"name": "example"}
        schema_path = "path/to/invalid_schema.json"

        # Calling the function and asserting exception
        with self.assertRaises(json.JSONDecodeError):
            validate(body, schema_path)

        mock_open.assert_called_once_with(schema_path)
        mock_json_load.assert_called_once()


if __name__ == "__main__":
    unittest.main()
