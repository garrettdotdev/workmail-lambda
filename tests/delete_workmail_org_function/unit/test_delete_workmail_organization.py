# tests/delete_workmail_org_function/unit/test_delete_workmail_organization.py
import unittest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError, BotoCoreError
from delete_workmail_org_function.app import delete_workmail_organization


class TestDeleteWorkmailOrganization(unittest.TestCase):

    def setUp(self):
        self.organization_id = "org-id"
        self.workmail_client = MagicMock()

    def test_delete_workmail_organization_success(self):
        self.workmail_client.delete_organization.return_value = {
            "OrganizationId": self.organization_id,
            "State": "DELETED",
        }

        response = delete_workmail_organization(
            self.organization_id, self.workmail_client
        )
        self.assertEqual(response["OrganizationId"], self.organization_id)
        self.assertEqual(response["State"], "DELETED")
        self.workmail_client.delete_organization.assert_called_once_with(
            ClientToken=unittest.mock.ANY,
            OrganizationId=self.organization_id,
            DeleteDirectory=True,
            ForceDelete=True,
        )

    @patch("delete_workmail_org_function.app.logger")
    def test_delete_workmail_organization_client_error(self, mock_logger):
        self.workmail_client.delete_organization.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Server Error"}}, "operation"
        )

        with self.assertRaises(ClientError):
            delete_workmail_organization(self.organization_id, self.workmail_client)
        mock_logger.error.assert_called_once()

    @patch("delete_workmail_org_function.app.logger")
    def test_delete_workmail_organization_boto_core_error(self, mock_logger):
        self.workmail_client.delete_organization.side_effect = BotoCoreError()

        with self.assertRaises(BotoCoreError):
            delete_workmail_organization(self.organization_id, self.workmail_client)
        mock_logger.error.assert_called_once()

    @patch("delete_workmail_org_function.app.logger")
    def test_delete_workmail_organization_unexpected_error(self, mock_logger):
        self.workmail_client.delete_organization.side_effect = Exception(
            "Unexpected error"
        )

        with self.assertRaises(Exception):
            delete_workmail_organization(self.organization_id, self.workmail_client)
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
