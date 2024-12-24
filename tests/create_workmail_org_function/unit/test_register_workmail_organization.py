# tests/create_workmail_org_function/unit/test_register_workmail_organization.py
import unittest
from unittest.mock import MagicMock
from create_workmail_org_function.app import register_workmail_organization


class TestRegisterWorkmailOrganization(unittest.TestCase):

    def test_register_workmail_organization_success(self):
        # Arrange
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        # Act
        register_workmail_organization(
            ownerid=1,
            email_username="testuser",
            vanity_name="testvanity",
            organization_id="test-org-id",
            connection=mock_connection,
        )

        # Assert
        mock_cursor.execute.assert_called_once_with(
            """INSERT INTO workmail_organizations (ownerid, email_username, vanity_name, organization_id, state) VALUES (%s, %s, %s, %s, %s)""",
            (1, "testuser", "testvanity", "test-org-id", "PENDING"),
        )
        mock_connection.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_register_workmail_organization_exception(self):
        # Arrange
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Test exception")
        mock_connection.cursor.return_value = mock_cursor

        # Act & Assert
        with self.assertRaises(Exception) as context:
            register_workmail_organization(
                ownerid=1,
                email_username="testuser",
                vanity_name="testvanity",
                organization_id="test-org-id",
                connection=mock_connection,
            )

        self.assertEqual(str(context.exception), "Test exception")
        mock_cursor.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
