# tests/workmail_create/unit/test_set_ses_notifications.py
import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError, BotoCoreError
from workmail_create.app import set_ses_notifications

# Set up constant test values
IDENTITY = "example.com"
CONFIG = {
    "SNS_BOUNCE_ARN": "arn:aws:sns:region:account-id:bounce-topic",
    "SNS_COMPLAINT_ARN": "arn:aws:sns:region:account-id:complaint-topic",
    "SNS_DELIVERY_ARN": "arn:aws:sns:region:account-id:delivery-topic",
}


@pytest.fixture
def mock_ses_client():
    return MagicMock()


def test_set_ses_notifications_success(mock_ses_client):
    """Test successful execution of set_ses_notifications."""
    # Act
    set_ses_notifications(IDENTITY, mock_ses_client, CONFIG)

    # Assert
    assert mock_ses_client.set_identity_notification_topic.call_count == 3
    mock_ses_client.set_identity_notification_topic.assert_any_call(
        Identity=IDENTITY,
        NotificationType="Bounce",
        SnsTopic=CONFIG["SNS_BOUNCE_ARN"],
    )
    mock_ses_client.set_identity_notification_topic.assert_any_call(
        Identity=IDENTITY,
        NotificationType="Complaint",
        SnsTopic=CONFIG["SNS_COMPLAINT_ARN"],
    )
    mock_ses_client.set_identity_notification_topic.assert_any_call(
        Identity=IDENTITY,
        NotificationType="Delivery",
        SnsTopic=CONFIG["SNS_DELIVERY_ARN"],
    )


def test_set_ses_notifications_client_error(mock_ses_client):
    """Test set_ses_notifications when ClientError is raised."""
    # Simulate ClientError
    mock_ses_client.set_identity_notification_topic.side_effect = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="SetIdentityNotificationTopic",
    )

    # Act & Assert
    with pytest.raises(ClientError) as excinfo:
        set_ses_notifications(IDENTITY, mock_ses_client, CONFIG)
    assert "Access Denied" in str(excinfo.value)
    assert mock_ses_client.set_identity_notification_topic.call_count == 1


def test_set_ses_notifications_botocore_error(mock_ses_client):
    """Test set_ses_notifications when BotoCoreError is raised."""
    # Simulate BotoCoreError
    mock_ses_client.set_identity_notification_topic.side_effect = BotoCoreError()

    # Act & Assert
    with pytest.raises(BotoCoreError) as excinfo:
        set_ses_notifications(IDENTITY, mock_ses_client, CONFIG)
    assert "An unspecified error occurred" in str(excinfo.value)
    assert mock_ses_client.set_identity_notification_topic.call_count == 1


def test_set_ses_notifications_unexpected_error(mock_ses_client):
    """Test set_ses_notifications when an unexpected error is raised."""
    # Simulate unexpected error
    mock_ses_client.set_identity_notification_topic.side_effect = Exception(
        "Unexpected error"
    )

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        set_ses_notifications(IDENTITY, mock_ses_client, CONFIG)
    assert "Unexpected error" in str(excinfo.value)
    assert mock_ses_client.set_identity_notification_topic.call_count == 1
