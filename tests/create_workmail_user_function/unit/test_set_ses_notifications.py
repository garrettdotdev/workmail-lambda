import unittest
from unittest.mock import MagicMock, patch
from create_workmail_user_function.app import set_ses_notifications


class TestSetSesNotifications(unittest.TestCase):

    def setUp(self):
        self.identity = "test@example.com"
        self.config = {
            "SNS_BOUNCE_ARN": "arn:aws:sns:us-east-1:123456789012:BounceTopic",
            "SNS_COMPLAINT_ARN": "arn:aws:sns:us-east-1:123456789012:ComplaintTopic",
            "SNS_DELIVERY_ARN": "arn:aws:sns:us-east-1:123456789012:DeliveryTopic",
        }
        self.ses_client = MagicMock()

    def test_set_ses_notifications_success(self):
        """Test setting SES notifications successfully."""
        set_ses_notifications(self.identity, self.ses_client, self.config)
        self.ses_client.set_identity_notification_topic.assert_any_call(
            Identity=self.identity,
            NotificationType="Bounce",
            SnsTopic=self.config["SNS_BOUNCE_ARN"],
        )
        self.ses_client.set_identity_notification_topic.assert_any_call(
            Identity=self.identity,
            NotificationType="Complaint",
            SnsTopic=self.config["SNS_COMPLAINT_ARN"],
        )
        self.ses_client.set_identity_notification_topic.assert_any_call(
            Identity=self.identity,
            NotificationType="Delivery",
            SnsTopic=self.config["SNS_DELIVERY_ARN"],
        )
        self.assertEqual(self.ses_client.set_identity_notification_topic.call_count, 3)

    @patch("create_workmail_user_function.app.logger")
    def test_set_ses_notifications_exception(self, mock_logger):
        """Test handling exceptions during setting SES notifications."""
        self.ses_client.set_identity_notification_topic.side_effect = Exception(
            "Test exception"
        )
        with self.assertRaises(Exception) as context:
            set_ses_notifications(self.identity, self.ses_client, self.config)
        self.assertEqual(str(context.exception), "Test exception")
        mock_logger.info.assert_any_call(
            f"Setting SES notifications for identity {self.identity}"
        )
        mock_logger.info.assert_any_call(
            f"Setting Bounce notification for {self.identity} with topic {self.config['SNS_BOUNCE_ARN']}"
        )


if __name__ == "__main__":
    unittest.main()
