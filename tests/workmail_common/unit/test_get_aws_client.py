import unittest
from unittest.mock import patch, MagicMock
from workmail_common.utils import get_aws_client
from botocore.exceptions import BotoCoreError, NoCredentialsError


class TestGetAwsClient(unittest.TestCase):

    @patch("workmail_common.utils.boto3.client")
    def test_get_aws_client_success(self, mock_boto_client):
        # Mock the client
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Call the function
        client = get_aws_client("s3")

        # Assertions
        mock_boto_client.assert_called_once_with("s3")
        self.assertEqual(client, mock_client)

    @patch("workmail_common.utils.boto3.client")
    def test_get_aws_client_boto_core_error(self, mock_boto_client):
        # Mock the client to raise a BotoCoreError
        mock_boto_client.side_effect = BotoCoreError()

        # Call the function and assert it raises an exception
        with self.assertRaises(BotoCoreError):
            get_aws_client("s3")

        mock_boto_client.assert_called_once_with("s3")

    @patch("workmail_common.utils.boto3.client")
    def test_get_aws_client_no_credentials_error(self, mock_boto_client):
        # Mock the client to raise a NoCredentialsError
        mock_boto_client.side_effect = NoCredentialsError()

        # Call the function and assert it raises an exception
        with self.assertRaises(NoCredentialsError):
            get_aws_client("s3")

        mock_boto_client.assert_called_once_with("s3")


if __name__ == "__main__":
    unittest.main()
