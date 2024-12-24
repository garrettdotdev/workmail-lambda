# tests/create_workmail_org_function/unit/test_get_dns_records.py
import unittest
from unittest.mock import patch, MagicMock
from create_workmail_org_function.app import get_dns_records


class TestGetDnsRecords(unittest.TestCase):

    @patch("create_workmail_org_function.app.boto3.client")
    def test_get_dns_records_success(self, mock_boto_client):
        # Arrange
        mock_workmail_client = MagicMock()
        mock_workmail_client.describe_mail_domain.return_value = {
            "Records": [
                {"Hostname": "test1.example.com", "Value": "value1"},
                {"Hostname": "test2.example.com", "Value": "value2"},
            ]
        }
        mock_boto_client.return_value = mock_workmail_client

        # Act
        result = get_dns_records("test-org-id", "example.com", mock_workmail_client)

        # Assert
        self.assertEqual(
            result,
            [
                {"Hostname": "test1.example.com", "Value": "value1"},
                {"Hostname": "test2.example.com", "Value": "value2"},
            ],
        )
        mock_workmail_client.describe_mail_domain.assert_called_once_with(
            OrganizationId="test-org-id", DomainName="example.com"
        )

    @patch("create_workmail_org_function.app.boto3.client")
    def test_get_dns_records_failure(self, mock_boto_client):
        # Arrange
        mock_workmail_client = MagicMock()
        mock_workmail_client.describe_mail_domain.return_value = {"Records": []}
        mock_boto_client.return_value = mock_workmail_client

        # Act
        result = get_dns_records("test-org-id", "example.com", mock_workmail_client)

        # Assert
        self.assertEqual(result, [])
        mock_workmail_client.describe_mail_domain.assert_called_once_with(
            OrganizationId="test-org-id", DomainName="example.com"
        )

    @patch("create_workmail_org_function.app.boto3.client")
    def test_get_dns_records_exception(self, mock_boto_client):
        # Arrange
        mock_workmail_client = MagicMock()
        mock_workmail_client.describe_mail_domain.side_effect = Exception(
            "Test exception"
        )
        mock_boto_client.return_value = mock_workmail_client

        # Act & Assert
        with self.assertRaises(Exception) as context:
            get_dns_records("test-org-id", "example.com", mock_workmail_client)

        self.assertEqual(str(context.exception), "Test exception")
        mock_workmail_client.describe_mail_domain.assert_called_once_with(
            OrganizationId="test-org-id", DomainName="example.com"
        )


if __name__ == "__main__":
    unittest.main()
