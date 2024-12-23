import unittest
from unittest.mock import patch, MagicMock
from workmail_common.utils import validate
from fastjsonschema import JsonSchemaException


class TestValidate(unittest.TestCase):

    @patch("fastjsonschema.compile")
    def test_validate_success(self, mock_compile):
        # Mock the validator
        mock_validator = MagicMock()
        mock_compile.return_value = mock_validator

        # Define a sample body and schema
        body = {"name": "test"}
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        # Call the function
        result = validate(body, schema)

        # Assertions
        mock_compile.assert_called_once_with(schema)
        mock_validator.assert_called_once_with(body)
        self.assertTrue(result)

    @patch("fastjsonschema.compile")
    def test_validate_json_schema_exception(self, mock_compile):
        # Mock the validator to raise a JsonSchemaException
        mock_validator = MagicMock()
        mock_compile.return_value = mock_validator
        mock_validator.side_effect = JsonSchemaException("Schema validation error")

        # Define a sample body and schema
        body = {"name": "test"}
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        # Call the function and assert it raises an exception
        with self.assertRaises(JsonSchemaException):
            validate(body, schema)

        mock_compile.assert_called_once_with(schema)
        mock_validator.assert_called_once_with(body)


if __name__ == "__main__":
    unittest.main()
