import unittest
from unittest.mock import patch, MagicMock
from workmail_common.utils import get_secret_value
from botocore.exceptions import BotoCoreError, NoCredentialsError, ClientError


class TestGetSecretValue(unittest.TestCase):

    @patch("workmail_common.utils.get_aws_client")
    def test_get_secret_value_success(self, mock_get_aws_client):
        # Mock the Secrets Manager client and its response
        mock_secretsmanager_client = MagicMock()
        mock_get_aws_client.return_value = mock_secretsmanager_client
        mock_secretsmanager_client.get_secret_value.return_value = {
            "SecretString": "my_secret_value"
        }

        # Call the function
        secret_value = get_secret_value("my_secret_name")

        # Assertions
        mock_get_aws_client.assert_called_once_with("secretsmanager")
        mock_secretsmanager_client.get_secret_value.assert_called_once_with(
            SecretId="my_secret_name"
        )
        self.assertEqual(secret_value, "my_secret_value")

    @patch("workmail_common.utils.get_aws_client")
    def test_get_secret_value_boto_core_error(self, mock_get_aws_client):
        # Mock the Secrets Manager client to raise a BotoCoreError
        mock_secretsmanager_client = MagicMock()
        mock_get_aws_client.return_value = mock_secretsmanager_client
        mock_secretsmanager_client.get_secret_value.side_effect = BotoCoreError()

        # Call the function and assert it raises an exception
        with self.assertRaises(BotoCoreError):
            get_secret_value("my_secret_name")

        mock_get_aws_client.assert_called_once_with("secretsmanager")
        mock_secretsmanager_client.get_secret_value.assert_called_once_with(
            SecretId="my_secret_name"
        )

    @patch("workmail_common.utils.get_aws_client")
    def test_get_secret_value_no_credentials_error(self, mock_get_aws_client):
        # Mock the Secrets Manager client to raise a NoCredentialsError
        mock_secretsmanager_client = MagicMock()
        mock_get_aws_client.return_value = mock_secretsmanager_client
        mock_secretsmanager_client.get_secret_value.side_effect = NoCredentialsError()

        # Call the function and assert it raises an exception
        with self.assertRaises(NoCredentialsError):
            get_secret_value("my_secret_name")

        mock_get_aws_client.assert_called_once_with("secretsmanager")
        mock_secretsmanager_client.get_secret_value.assert_called_once_with(
            SecretId="my_secret_name"
        )

    @patch("workmail_common.utils.get_aws_client")
    def test_get_secret_value_client_error(self, mock_get_aws_client):
        # Mock the Secrets Manager client to raise a ClientError
        mock_secretsmanager_client = MagicMock()
        mock_get_aws_client.return_value = mock_secretsmanager_client
        mock_secretsmanager_client.get_secret_value.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Secret not found",
                }
            },
            operation_name="GetSecretValue",
        )

        # Call the function and assert it raises an exception
        with self.assertRaises(ClientError):
            get_secret_value("my_secret_name")

        mock_get_aws_client.assert_called_once_with("secretsmanager")
        mock_secretsmanager_client.get_secret_value.assert_called_once_with(
            SecretId="my_secret_name"
        )


if __name__ == "__main__":
    unittest.main()
