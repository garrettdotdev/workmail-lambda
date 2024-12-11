# tests/workmail_common/unit/test_load_schema.py
import unittest
from unittest.mock import patch, mock_open
from workmail_common.utils import load_schema
import json


class TestLoadSchema(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data='{"type": "object"}')
    def test_load_schema_success(self, mock_file):
        # Act
        schema = load_schema("schema.json")

        # Assert
        self.assertEqual(schema, {"type": "object"})
        mock_file.assert_called_once_with("schema.json")

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_schema_file_not_found(self, mock_file):
        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            load_schema("non_existent_schema.json")
        mock_file.assert_called_once_with("non_existent_schema.json")

    @patch("builtins.open", new_callable=mock_open, read_data='{"type": "object"')
    def test_load_schema_json_decode_error(self, mock_file):
        # Act & Assert
        with self.assertRaises(json.JSONDecodeError):
            load_schema("invalid_schema.json")
        mock_file.assert_called_once_with("invalid_schema.json")

    @patch("builtins.open", side_effect=Exception("Unexpected error"))
    def test_load_schema_unexpected_error(self, mock_file):
        # Act & Assert
        with self.assertRaises(Exception) as context:
            load_schema("schema.json")
        self.assertTrue("Unexpected error" in str(context.exception))
        mock_file.assert_called_once_with("schema.json")


if __name__ == "__main__":
    unittest.main()
