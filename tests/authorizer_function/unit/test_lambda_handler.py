import unittest
from unittest.mock import patch, MagicMock
import json
import os
from authorizer_function.app import lambda_handler


class TestLambdaHandler(unittest.TestCase):

    @patch.dict(os.environ, {"TOKEN_SECRET_NAME": "test_secret_name"})
    @patch("authorizer_function.app.get_secret_value")
    def test_lambda_handler_authorized(self, mock_get_secret_value):
        event = {"headers": {"Authorization": "Bearer valid_token"}}
        context = {}

        mock_get_secret_value.return_value = "valid_token"

        response = lambda_handler(event, context)
        self.assertTrue(response["isAuthorized"])

    @patch.dict(os.environ, {"TOKEN_SECRET_NAME": "test_secret_name"})
    @patch("authorizer_function.app.get_secret_value")
    def test_lambda_handler_unauthorized_invalid_token(self, mock_get_secret_value):
        event = {"headers": {"Authorization": "Bearer invalid_token"}}
        context = {}

        mock_get_secret_value.return_value = "valid_token"

        response = lambda_handler(event, context)
        self.assertFalse(response["isAuthorized"])

    @patch.dict(os.environ, {"TOKEN_SECRET_NAME": "test_secret_name"})
    @patch("authorizer_function.app.get_secret_value")
    def test_lambda_handler_no_token(self, mock_get_secret_value):
        event = {"headers": {}}
        context = {}

        response = lambda_handler(event, context)
        self.assertFalse(response["isAuthorized"])

    @patch.dict(os.environ, {"TOKEN_SECRET_NAME": "test_secret_name"})
    @patch("authorizer_function.app.get_secret_value")
    def test_lambda_handler_no_secret_name(self, mock_get_secret_value):
        event = {"headers": {"Authorization": "Bearer valid_token"}}
        context = {}

        with patch.dict(os.environ, {}, clear=True):
            response = lambda_handler(event, context)
            self.assertFalse(response["isAuthorized"])

    @patch.dict(os.environ, {"TOKEN_SECRET_NAME": "test_secret_name"})
    @patch("authorizer_function.app.get_secret_value")
    def test_lambda_handler_exception(self, mock_get_secret_value):
        event = {"headers": {"Authorization": "Bearer valid_token"}}
        context = {}

        mock_get_secret_value.side_effect = Exception("Test exception")

        response = lambda_handler(event, context)
        self.assertFalse(response["isAuthorized"])


if __name__ == "__main__":
    unittest.main()
