import unittest
from unittest.mock import patch, MagicMock
from workmail_cancel.app import get_aws_clients


class TestGetAwsClients(unittest.TestCase):
    @patch("workmail_cancel.app.boto3.client")
    def test_get_aws_clients(self, mock_boto_client):
        # Arrange
        mock_rds_client = MagicMock()
        mock_cloudformation_client = MagicMock()
        mock_boto_client.side_effect = [mock_rds_client, mock_cloudformation_client]
        region_name = "us-east-1"

        # Act
        clients = get_aws_clients(region_name)

        # Assert
        mock_boto_client.assert_any_call("rds-data", region_name=region_name)
        mock_boto_client.assert_any_call("cloudformation", region_name=region_name)
        self.assertEqual(clients["rds_client"], mock_rds_client)
        self.assertEqual(clients["cloudformation_client"], mock_cloudformation_client)

    @patch("workmail_cancel.app.boto3.client")
    def test_get_aws_clients_different_region(self, mock_boto_client):
        # Arrange
        mock_rds_client = MagicMock()
        mock_cloudformation_client = MagicMock()
        mock_boto_client.side_effect = [mock_rds_client, mock_cloudformation_client]
        region_name = "us-west-2"

        # Act
        clients = get_aws_clients(region_name)

        # Assert
        mock_boto_client.assert_any_call("rds-data", region_name=region_name)
        mock_boto_client.assert_any_call("cloudformation", region_name=region_name)
        self.assertEqual(clients["rds_client"], mock_rds_client)
        self.assertEqual(clients["cloudformation_client"], mock_cloudformation_client)

    @patch("workmail_cancel.app.boto3.client")
    def test_get_aws_clients_no_region(self, mock_boto_client):
        # Arrange
        mock_rds_client = MagicMock()
        mock_cloudformation_client = MagicMock()
        mock_boto_client.side_effect = [mock_rds_client, mock_cloudformation_client]

        # Act
        clients = get_aws_clients(None)

        # Assert
        mock_boto_client.assert_any_call("rds-data", region_name=None)
        mock_boto_client.assert_any_call("cloudformation", region_name=None)
        self.assertEqual(clients["rds_client"], mock_rds_client)
        self.assertEqual(clients["cloudformation_client"], mock_cloudformation_client)

    @patch("workmail_cancel.app.boto3.client")
    def test_get_aws_clients_exception_handling(self, mock_boto_client):
        # Arrange
        mock_boto_client.side_effect = Exception("Boto3 client error")
        region_name = "us-east-1"

        # Act & Assert
        with self.assertRaises(Exception) as context:
            get_aws_clients(region_name)
        self.assertTrue("Boto3 client error" in str(context.exception))


if __name__ == "__main__":
    unittest.main()
