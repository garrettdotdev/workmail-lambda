import unittest
from unittest.mock import patch, mock_open
from workmail_common.utils import load_schema
import json


class TestLoadSchema(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{"type": "object"}')
    def test_load_schema_success(self, mock_file):
        schema_path = "schema.json"
        schema = load_schema(schema_path)
        self.assertEqual(schema, {"type": "object"})
        mock_file.assert_called_once_with(schema_path)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_schema_file_not_found(self, mock_file):
        schema_path = "non_existent_schema.json"
        with self.assertRaises(FileNotFoundError):
            load_schema(schema_path)
        mock_file.assert_called_once_with(schema_path)

    @patch("builtins.open", new_callable=mock_open, read_data='{"type": "object"')
    def test_load_schema_json_decode_error(self, mock_file):
        schema_path = "invalid_schema.json"
        with self.assertRaises(json.JSONDecodeError):
            load_schema(schema_path)
        mock_file.assert_called_once_with(schema_path)


if __name__ == "__main__":
    unittest.main()
