import unittest
from unittest.mock import patch, MagicMock
from workmail_cancel.app import delete_workmail_stack
from botocore.exceptions import ClientError, BotoCoreError


class TestDeleteWorkmailStack(unittest.TestCase):
    @patch("workmail_cancel.app.boto3.client")
    def test_delete_workmail_stack_success(self, mock_boto_client):
        # Arrange
        mock_cloudformation_client = MagicMock()
        mock_boto_client.return_value = mock_cloudformation_client
        stack_id = "stack123"

        # Act
        delete_workmail_stack(stack_id, mock_cloudformation_client)

        # Assert
        mock_cloudformation_client.delete_stack.assert_called_once_with(
            StackName=stack_id
        )

    @patch("workmail_cancel.app.boto3.client")
    def test_delete_workmail_stack_client_error(self, mock_boto_client):
        # Arrange
        mock_cloudformation_client = MagicMock()
        mock_boto_client.return_value = mock_cloudformation_client
        mock_cloudformation_client.delete_stack.side_effect = ClientError(
            {"Error": {"Code": "ClientError", "Message": "An error occurred"}},
            "delete_stack",
        )
        stack_id = "stack123"

        # Act & Assert
        with self.assertRaises(ClientError) as context:
            delete_workmail_stack(stack_id, mock_cloudformation_client)
        self.assertTrue("An error occurred" in str(context.exception))
        mock_cloudformation_client.delete_stack.assert_called_once_with(
            StackName=stack_id
        )

    @patch("workmail_cancel.app.boto3.client")
    def test_delete_workmail_stack_boto_core_error(self, mock_boto_client):
        # Arrange
        mock_cloudformation_client = MagicMock()
        mock_boto_client.return_value = mock_cloudformation_client
        mock_cloudformation_client.delete_stack.side_effect = BotoCoreError()
        stack_id = "stack123"

        # Act & Assert
        with self.assertRaises(BotoCoreError) as context:
            delete_workmail_stack(stack_id, mock_cloudformation_client)
        self.assertTrue(isinstance(context.exception, BotoCoreError))
        mock_cloudformation_client.delete_stack.assert_called_once_with(
            StackName=stack_id
        )

    @patch("workmail_cancel.app.boto3.client")
    def test_delete_workmail_stack_unexpected_error(self, mock_boto_client):
        # Arrange
        mock_cloudformation_client = MagicMock()
        mock_boto_client.return_value = mock_cloudformation_client
        mock_cloudformation_client.delete_stack.side_effect = Exception(
            "Unexpected error"
        )
        stack_id = "stack123"

        # Act & Assert
        with self.assertRaises(Exception) as context:
            delete_workmail_stack(stack_id, mock_cloudformation_client)
        self.assertTrue("Unexpected error" in str(context.exception))
        mock_cloudformation_client.delete_stack.assert_called_once_with(
            StackName=stack_id
        )


if __name__ == "__main__":
    unittest.main()
