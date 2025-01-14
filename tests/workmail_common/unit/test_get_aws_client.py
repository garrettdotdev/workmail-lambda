# tests/workmail_common/unit/test_get_aws_client.py
import unittest
import socket
from unittest.mock import patch, MagicMock
from botocore.exceptions import BotoCoreError, NoCredentialsError
from workmail_common.utils import get_aws_client


class TestGetAwsClient(unittest.TestCase):

    @patch("workmail_common.utils.boto3.client")
    @patch("workmail_common.utils.socket.gethostbyname")
    def test_get_aws_client_success(self, mock_gethostbyname, mock_boto_client):
        # Arrange
        mock_client = MagicMock()
        mock_client.meta.endpoint_url = "https://service.us-east-1.amazonaws.com"
        mock_boto_client.return_value = mock_client
        mock_gethostbyname.return_value = "127.0.0.1"

        # Act
        client = get_aws_client("s3")

        # Assert
        mock_boto_client.assert_called_once_with("s3", config=unittest.mock.ANY)
        mock_gethostbyname.assert_called_once_with("service.us-east-1.amazonaws.com")
        self.assertEqual(client, mock_client)

    @patch("workmail_common.utils.boto3.client")
    @patch("workmail_common.utils.socket.gethostbyname")
    def test_get_aws_client_no_credentials_error(
        self, mock_gethostbyname, mock_boto_client
    ):
        # Arrange
        mock_boto_client.side_effect = NoCredentialsError()

        # Act & Assert
        with self.assertRaises(NoCredentialsError):
            get_aws_client("s3")

        mock_boto_client.assert_called_once_with("s3", config=unittest.mock.ANY)
        mock_gethostbyname.assert_not_called()

    @patch("workmail_common.utils.boto3.client")
    @patch("workmail_common.utils.socket.gethostbyname")
    def test_get_aws_client_boto_core_error(self, mock_gethostbyname, mock_boto_client):
        # Arrange
        mock_boto_client.side_effect = BotoCoreError()

        # Act & Assert
        with self.assertRaises(BotoCoreError):
            get_aws_client("s3")

        mock_boto_client.assert_called_once_with("s3", config=unittest.mock.ANY)
        mock_gethostbyname.assert_not_called()

    @patch("workmail_common.utils.boto3.client")
    @patch("workmail_common.utils.socket.gethostbyname")
    def test_get_aws_client_socket_error(self, mock_gethostbyname, mock_boto_client):
        # Arrange
        mock_client = MagicMock()
        mock_client.meta.endpoint_url = "https://service.us-east-1.amazonaws.com"
        mock_boto_client.return_value = mock_client
        mock_gethostbyname.side_effect = socket.error()

        # Act & Assert
        with self.assertRaises(socket.error):
            get_aws_client("s3")

        mock_boto_client.assert_called_once_with("s3", config=unittest.mock.ANY)
        mock_gethostbyname.assert_called_once_with("service.us-east-1.amazonaws.com")


if __name__ == "__main__":
    unittest.main()
