import unittest
from unittest.mock import patch, MagicMock
from workmail_common.utils import get_account_id
from botocore.exceptions import BotoCoreError, NoCredentialsError


class TestGetAccountId(unittest.TestCase):

    @patch("workmail_common.utils.boto3.client")
    def test_get_account_id_success(self, mock_boto_client):
        # Mock the STS client and its response
        mock_sts_client = MagicMock()
        mock_boto_client.return_value = mock_sts_client
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Call the function
        account_id = get_account_id()

        # Assertions
        mock_boto_client.assert_called_once_with("sts")
        mock_sts_client.get_caller_identity.assert_called_once()
        self.assertEqual(account_id, "123456789012")

    @patch("workmail_common.utils.boto3.client")
    def test_get_account_id_boto_core_error(self, mock_boto_client):
        # Mock the STS client to raise a BotoCoreError
        mock_sts_client = MagicMock()
        mock_boto_client.return_value = mock_sts_client
        mock_sts_client.get_caller_identity.side_effect = BotoCoreError()

        # Call the function and assert it raises an exception
        with self.assertRaises(BotoCoreError):
            get_account_id()

        mock_boto_client.assert_called_once_with("sts")
        mock_sts_client.get_caller_identity.assert_called_once()

    @patch("workmail_common.utils.boto3.client")
    def test_get_account_id_no_credentials_error(self, mock_boto_client):
        # Mock the STS client to raise a NoCredentialsError
        mock_sts_client = MagicMock()
        mock_boto_client.return_value = mock_sts_client
        mock_sts_client.get_caller_identity.side_effect = NoCredentialsError()

        # Call the function and assert it raises an exception
        with self.assertRaises(NoCredentialsError):
            get_account_id()

        mock_boto_client.assert_called_once_with("sts")
        mock_sts_client.get_caller_identity.assert_called_once()


if __name__ == "__main__":
    unittest.main()
