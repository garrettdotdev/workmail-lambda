import unittest
from unittest.mock import patch, MagicMock
from workmail_common.utils import connect_to_rds


class TestConnectToRds(unittest.TestCase):

    @patch("workmail_common.utils.mysql.connector.connect")
    @patch("workmail_common.utils.json.loads")
    @patch("workmail_common.utils.boto3.client")
    def test_connect_to_rds_success(
        self, mock_boto_client, mock_json_loads, mock_mysql_connect
    ):
        # Mock the secret manager client and its response
        mock_secret_manager_client = MagicMock()
        mock_boto_client.return_value = mock_secret_manager_client
        mock_secret_manager_client.get_secret_value.return_value = {
            "SecretString": '{"username": "test_user", "password": "test_pass", "host": "test_host"}'
        }

        # Mock the json.loads to return a dictionary
        mock_json_loads.return_value = {
            "username": "test_user",
            "password": "test_pass",
            "host": "test_host",
        }

        # Mock the MySQL connection
        mock_connection = MagicMock()
        mock_mysql_connect.return_value = mock_connection

        # Define the config
        config = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
            "DATABASE_NAME": "test_db",
        }

        # Call the function
        connection = connect_to_rds(mock_secret_manager_client, config)

        # Assertions
        mock_secret_manager_client.get_secret_value.assert_called_once_with(
            SecretId=config["DB_SECRET_ARN"]
        )
        mock_json_loads.assert_called_once_with(
            mock_secret_manager_client.get_secret_value.return_value["SecretString"]
        )
        mock_mysql_connect.assert_called_once_with(
            user="test_user", password="test_pass", host="test_host", database="test_db"
        )
        self.assertEqual(connection, mock_connection)

    @patch("workmail_common.utils.mysql.connector.connect")
    @patch("workmail_common.utils.json.loads")
    @patch("workmail_common.utils.boto3.client")
    def test_connect_to_rds_secret_manager_exception(
        self, mock_boto_client, mock_json_loads, mock_mysql_connect
    ):
        # Mock the secret manager client to raise an exception
        mock_secret_manager_client = MagicMock()
        mock_boto_client.return_value = mock_secret_manager_client
        mock_secret_manager_client.get_secret_value.side_effect = Exception(
            "Secret manager error"
        )

        # Define the config
        config = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
            "DATABASE_NAME": "test_db",
        }

        # Call the function and assert it raises an exception
        with self.assertRaises(Exception) as context:
            connect_to_rds(mock_secret_manager_client, config)

        self.assertEqual(str(context.exception), "Secret manager error")
        mock_secret_manager_client.get_secret_value.assert_called_once_with(
            SecretId=config["DB_SECRET_ARN"]
        )
        mock_json_loads.assert_not_called()
        mock_mysql_connect.assert_not_called()

    @patch("workmail_common.utils.mysql.connector.connect")
    @patch("workmail_common.utils.json.loads")
    @patch("workmail_common.utils.boto3.client")
    def test_connect_to_rds_mysql_exception(
        self, mock_boto_client, mock_json_loads, mock_mysql_connect
    ):
        # Mock the secret manager client and its response
        mock_secret_manager_client = MagicMock()
        mock_boto_client.return_value = mock_secret_manager_client
        mock_secret_manager_client.get_secret_value.return_value = {
            "SecretString": '{"username": "test_user", "password": "test_pass", "host": "test_host"}'
        }

        # Mock the json.loads to return a dictionary
        mock_json_loads.return_value = {
            "username": "test_user",
            "password": "test_pass",
            "host": "test_host",
        }

        # Mock the MySQL connection to raise an exception
        mock_mysql_connect.side_effect = Exception("MySQL connection error")

        # Define the config
        config = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
            "DATABASE_NAME": "test_db",
        }

        # Call the function and assert it raises an exception
        with self.assertRaises(Exception) as context:
            connect_to_rds(mock_secret_manager_client, config)

        self.assertEqual(str(context.exception), "MySQL connection error")
        mock_secret_manager_client.get_secret_value.assert_called_once_with(
            SecretId=config["DB_SECRET_ARN"]
        )
        mock_json_loads.assert_called_once_with(
            mock_secret_manager_client.get_secret_value.return_value["SecretString"]
        )
        mock_mysql_connect.assert_called_once_with(
            user="test_user", password="test_pass", host="test_host", database="test_db"
        )


if __name__ == "__main__":
    unittest.main()
