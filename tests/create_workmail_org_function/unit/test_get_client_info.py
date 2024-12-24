# tests/create_workmail_org_function/unit/test_get_client_info.py
import unittest
from unittest.mock import patch, MagicMock
from create_workmail_org_function.app import get_client_info


class TestGetClientInfo(unittest.TestCase):

    @patch("create_workmail_org_function.app.connect_to_rds")
    def test_get_client_info_success(self, mock_connect_to_rds):
        # Arrange
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("John", "Doe")
        mock_connection.cursor.return_value = mock_cursor
        mock_connect_to_rds.return_value = mock_connection

        # Act
        first_name, last_name = get_client_info(1, "test-app", mock_connection)

        # Assert
        self.assertEqual(first_name, "John")
        self.assertEqual(last_name, "Doe")
        mock_cursor.execute.assert_called_once_with(
            """SELECT ownerfirstname, ownerlastname FROM app WHERE ownerid = %s AND appname = %s LIMIT 1""",
            (1, "test-app"),
        )
        mock_cursor.close.assert_called_once()

    @patch("create_workmail_org_function.app.connect_to_rds")
    def test_get_client_info_no_result(self, mock_connect_to_rds):
        # Arrange
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_connect_to_rds.return_value = mock_connection

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            get_client_info(1, "test-app", mock_connection)

        self.assertEqual(
            str(context.exception),
            "No client found with contact_id 1 and appname test-app",
        )
        mock_cursor.execute.assert_called_once_with(
            """SELECT ownerfirstname, ownerlastname FROM app WHERE ownerid = %s AND appname = %s LIMIT 1""",
            (1, "test-app"),
        )
        mock_cursor.close.assert_called_once()

    @patch("create_workmail_org_function.app.connect_to_rds")
    def test_get_client_info_exception(self, mock_connect_to_rds):
        # Arrange
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Test exception")
        mock_connection.cursor.return_value = mock_cursor
        mock_connect_to_rds.return_value = mock_connection

        # Act & Assert
        with self.assertRaises(Exception) as context:
            get_client_info(1, "test-app", mock_connection)

        self.assertEqual(str(context.exception), "Test exception")
        mock_cursor.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
