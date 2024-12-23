import unittest
from unittest.mock import patch, MagicMock
from workmail_common.utils import get_aws_clients
from botocore.exceptions import BotoCoreError, NoCredentialsError


class TestGetAwsClients(unittest.TestCase):

    @patch("workmail_common.utils.boto3.client")
    def test_get_aws_clients_success(self, mock_boto_client):
        # Mock the clients
        mock_secretsmanager_client = MagicMock()
        mock_ses_client = MagicMock()
        mock_workmail_client = MagicMock()

        mock_boto_client.side_effect = [
            mock_secretsmanager_client,
            mock_ses_client,
            mock_workmail_client,
        ]

        # Call the function
        clients = get_aws_clients()

        # Assertions
        self.assertEqual(clients["secretsmanager_client"], mock_secretsmanager_client)
        self.assertEqual(clients["ses_client"], mock_ses_client)
        self.assertEqual(clients["workmail_client"], mock_workmail_client)
        mock_boto_client.assert_any_call("secretsmanager", config=unittest.mock.ANY)
        mock_boto_client.assert_any_call("ses", config=unittest.mock.ANY)
        mock_boto_client.assert_any_call("workmail", config=unittest.mock.ANY)

    @patch("workmail_common.utils.boto3.client")
    def test_get_aws_clients_boto_core_error(self, mock_boto_client):
        # Mock the client to raise a BotoCoreError
        mock_boto_client.side_effect = BotoCoreError()

        # Call the function and assert it raises an exception
        with self.assertRaises(BotoCoreError):
            get_aws_clients()

        mock_boto_client.assert_called_once_with(
            "secretsmanager", config=unittest.mock.ANY
        )

    @patch("workmail_common.utils.boto3.client")
    def test_get_aws_clients_no_credentials_error(self, mock_boto_client):
        # Mock the client to raise a NoCredentialsError
        mock_boto_client.side_effect = NoCredentialsError()

        # Call the function and assert it raises an exception
        with self.assertRaises(NoCredentialsError):
            get_aws_clients()

        mock_boto_client.assert_called_once_with(
            "secretsmanager", config=unittest.mock.ANY
        )


if __name__ == "__main__":
    unittest.main()
