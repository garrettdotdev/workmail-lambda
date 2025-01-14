# tests/delete_workmail_org_function/unit/test_get_workmail_organization_id.py
import unittest
from unittest.mock import MagicMock, patch
from delete_workmail_org_function.app import get_workmail_organization_id
from botocore.exceptions import ClientError, BotoCoreError


class TestGetWorkmailOrganizationId(unittest.TestCase):

    def setUp(self):
        self.contact_id = 1
        self.vanity_name = "example"
        self.connection = MagicMock()

    def test_get_workmail_organization_id_success(self):
        cursor = self.connection.cursor.return_value
        cursor.fetchone.return_value = "org-id"

        organization_id = get_workmail_organization_id(
            self.contact_id, self.vanity_name, self.connection
        )
        self.assertEqual(organization_id, "org-id")
        cursor.execute.assert_called_once_with(
            """SELECT organization_id FROM workmail_organizations WHERE ownerid = %s AND vanity_name = %s LIMIT 1""",
            (self.contact_id, self.vanity_name),
        )

    def test_get_workmail_organization_id_not_found(self):
        cursor = self.connection.cursor.return_value
        cursor.fetchone.return_value = None

        with self.assertRaises(ValueError) as context:
            get_workmail_organization_id(
                self.contact_id, self.vanity_name, self.connection
            )
        self.assertIn(
            "No WorkMail organization_id found with contact_id=1 and vanity_name=example",
            str(context.exception),
        )

    @patch("delete_workmail_org_function.app.logger")
    def test_get_workmail_organization_id_client_error(self, mock_logger):
        self.connection.cursor.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Server Error"}}, "operation"
        )

        with self.assertRaises(ClientError):
            get_workmail_organization_id(
                self.contact_id, self.vanity_name, self.connection
            )
        mock_logger.error.assert_called_once()

    @patch("delete_workmail_org_function.app.logger")
    def test_get_workmail_organization_id_boto_core_error(self, mock_logger):
        self.connection.cursor.side_effect = BotoCoreError()

        with self.assertRaises(BotoCoreError):
            get_workmail_organization_id(
                self.contact_id, self.vanity_name, self.connection
            )
        mock_logger.error.assert_called_once()

    @patch("delete_workmail_org_function.app.logger")
    def test_get_workmail_organization_id_unexpected_error(self, mock_logger):
        self.connection.cursor.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception):
            get_workmail_organization_id(
                self.contact_id, self.vanity_name, self.connection
            )
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
