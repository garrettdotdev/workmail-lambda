# tests/create_workmail_org_function/unit/test_create_workmail_org.py
import unittest
from unittest.mock import patch, MagicMock
from create_workmail_org_function.app import create_workmail_org


class TestCreateWorkmailOrg(unittest.TestCase):

    @patch("create_workmail_org_function.app.time.sleep", return_value=None)
    @patch(
        "create_workmail_org_function.app.uuid.uuid4", return_value="test-client-token"
    )
    def test_create_workmail_org_success(self, mock_uuid, mock_sleep):
        # Arrange
        mock_workmail_client = MagicMock()
        mock_workmail_client.create_organization.return_value = {
            "OrganizationId": "test-org-id"
        }
        mock_workmail_client.describe_organization.side_effect = [
            {"State": "PENDING"},
            {"State": "ACTIVE"},
        ]

        # Act
        result = create_workmail_org(
            organization_name="test-org",
            vanity_name="test-vanity",
            workmail_client=mock_workmail_client,
        )

        # Assert
        self.assertEqual(result, {"organization_id": "test-org-id"})
        mock_workmail_client.create_organization.assert_called_once_with(
            Alias="test-org", ClientToken="test-client-token"
        )
        self.assertEqual(mock_workmail_client.describe_organization.call_count, 2)
        mock_workmail_client.register_mail_domain.assert_called_once_with(
            ClientToken="test-client-token",
            OrganizationId="test-org-id",
            DomainName="test-vanity",
        )

    @patch("create_workmail_org_function.app.time.sleep", return_value=None)
    @patch(
        "create_workmail_org_function.app.uuid.uuid4", return_value="test-client-token"
    )
    def test_create_workmail_org_failure(self, mock_uuid, mock_sleep):
        # Arrange
        mock_workmail_client = MagicMock()
        mock_workmail_client.create_organization.return_value = {
            "OrganizationId": "test-org-id"
        }
        mock_workmail_client.describe_organization.side_effect = [
            {"State": "PENDING"},
            {"State": "FAILED", "ErrorMessage": "Test error message"},
        ]

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            create_workmail_org(
                organization_name="test-org",
                vanity_name="test-vanity",
                workmail_client=mock_workmail_client,
            )

        self.assertEqual(
            str(context.exception),
            "Organization test-org-id creation failed: Test error message",
        )
        mock_workmail_client.create_organization.assert_called_once_with(
            Alias="test-org", ClientToken="test-client-token"
        )
        self.assertEqual(mock_workmail_client.describe_organization.call_count, 2)

    @patch("create_workmail_org_function.app.time.sleep", return_value=None)
    @patch(
        "create_workmail_org_function.app.uuid.uuid4", return_value="test-client-token"
    )
    def test_create_workmail_org_timeout(self, mock_uuid, mock_sleep):
        # Arrange
        mock_workmail_client = MagicMock()
        mock_workmail_client.create_organization.return_value = {
            "OrganizationId": "test-org-id"
        }
        mock_workmail_client.describe_organization.side_effect = [
            {"State": "PENDING"}
        ] * 12  # Ensure enough items

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            create_workmail_org(
                organization_name="test-org",
                vanity_name="test-vanity",
                workmail_client=mock_workmail_client,
            )

        self.assertEqual(
            str(context.exception),
            "Organization test-org-id took too long to become Active",
        )
        mock_workmail_client.create_organization.assert_called_once_with(
            Alias="test-org", ClientToken="test-client-token"
        )
        self.assertEqual(mock_workmail_client.describe_organization.call_count, 12)

    @patch("create_workmail_org_function.app.time.sleep", return_value=None)
    @patch(
        "create_workmail_org_function.app.uuid.uuid4", return_value="test-client-token"
    )
    def test_create_workmail_org_exception(self, mock_uuid, mock_sleep):
        # Arrange
        mock_workmail_client = MagicMock()
        mock_workmail_client.create_organization.side_effect = Exception(
            "Test exception"
        )

        # Act & Assert
        with self.assertRaises(Exception) as context:
            create_workmail_org(
                organization_name="test-org",
                vanity_name="test-vanity",
                workmail_client=mock_workmail_client,
            )

        self.assertEqual(str(context.exception), "Test exception")
        mock_workmail_client.create_organization.assert_called_once_with(
            Alias="test-org", ClientToken="test-client-token"
        )


if __name__ == "__main__":
    unittest.main()
