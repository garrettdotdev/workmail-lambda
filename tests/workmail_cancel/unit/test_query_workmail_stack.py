import unittest
from unittest.mock import patch, MagicMock
from workmail_cancel.app import query_workmail_stack
from botocore.exceptions import ClientError, BotoCoreError


class TestQueryWorkmailStack(unittest.TestCase):
    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.boto3.client")
    def test_query_workmail_stack_success(self, mock_boto_client, mock_get_config):
        # Arrange
        mock_rds_client = MagicMock()
        mock_boto_client.return_value = mock_rds_client
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:mysecret",
            "DB_CLUSTER_ARN": "arn:aws:rds:us-east-1:123456789012:cluster:mycluster",
            "DATABASE_NAME": "mydatabase",
        }
        mock_rds_client.execute_statement.return_value = {
            "records": [[{"stringValue": "stack123"}]]
        }
        contact_id = 1
        appname = "myapp"

        # Act
        stack_id = query_workmail_stack(
            contact_id, appname, mock_rds_client, mock_get_config.return_value
        )

        # Assert
        self.assertEqual(stack_id, "stack123")
        mock_rds_client.execute_statement.assert_called_once()

    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.boto3.client")
    def test_query_workmail_stack_no_records(self, mock_boto_client, mock_get_config):
        # Arrange
        mock_rds_client = MagicMock()
        mock_boto_client.return_value = mock_rds_client
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:mysecret",
            "DB_CLUSTER_ARN": "arn:aws:rds:us-east-1:123456789012:cluster:mycluster",
            "DATABASE_NAME": "mydatabase",
        }
        mock_rds_client.execute_statement.return_value = {"records": []}
        contact_id = 1
        appname = "myapp"

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            query_workmail_stack(
                contact_id, appname, mock_rds_client, mock_get_config.return_value
            )
        self.assertTrue("No WorkMail stack found" in str(context.exception))
        mock_rds_client.execute_statement.assert_called_once()

    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.boto3.client")
    def test_query_workmail_stack_client_error(self, mock_boto_client, mock_get_config):
        # Arrange
        mock_rds_client = MagicMock()
        mock_boto_client.return_value = mock_rds_client
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:mysecret",
            "DB_CLUSTER_ARN": "arn:aws:rds:us-east-1:123456789012:cluster:mycluster",
            "DATABASE_NAME": "mydatabase",
        }
        mock_rds_client.execute_statement.side_effect = ClientError(
            {"Error": {"Code": "ClientError", "Message": "An error occurred"}},
            "execute_statement",
        )
        contact_id = 1
        appname = "myapp"

        # Act & Assert
        with self.assertRaises(ClientError) as context:
            query_workmail_stack(
                contact_id, appname, mock_rds_client, mock_get_config.return_value
            )
        self.assertTrue("An error occurred" in str(context.exception))
        mock_rds_client.execute_statement.assert_called_once()

    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.boto3.client")
    def test_query_workmail_stack_boto_core_error(
        self, mock_boto_client, mock_get_config
    ):
        # Arrange
        mock_rds_client = MagicMock()
        mock_boto_client.return_value = mock_rds_client
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:mysecret",
            "DB_CLUSTER_ARN": "arn:aws:rds:us-east-1:123456789012:cluster:mycluster",
            "DATABASE_NAME": "mydatabase",
        }
        mock_rds_client.execute_statement.side_effect = BotoCoreError()
        contact_id = 1
        appname = "myapp"

        # Act & Assert
        with self.assertRaises(BotoCoreError) as context:
            query_workmail_stack(
                contact_id, appname, mock_rds_client, mock_get_config.return_value
            )
        self.assertTrue(isinstance(context.exception, BotoCoreError))

    @patch("workmail_cancel.app.get_config")
    @patch("workmail_cancel.app.boto3.client")
    def test_query_workmail_stack_unexpected_error(
        self, mock_boto_client, mock_get_config
    ):
        # Arrange
        mock_rds_client = MagicMock()
        mock_boto_client.return_value = mock_rds_client
        mock_get_config.return_value = {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:mysecret",
            "DB_CLUSTER_ARN": "arn:aws:rds:us-east-1:123456789012:cluster:mycluster",
            "DATABASE_NAME": "mydatabase",
        }
        mock_rds_client.execute_statement.side_effect = Exception("Unexpected error")
        contact_id = 1
        appname = "myapp"

        # Act & Assert
        with self.assertRaises(Exception) as context:
            query_workmail_stack(
                contact_id, appname, mock_rds_client, mock_get_config.return_value
            )
        self.assertTrue("Unexpected error" in str(context.exception))
        mock_rds_client.execute_statement.assert_called_once()


if __name__ == "__main__":
    unittest.main()
