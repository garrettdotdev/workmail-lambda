# tests/workmail_create/unit/test_register_workmail_stack.py
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError, BotoCoreError
from workmail_create.app import register_workmail_stack
from workmail_create.config import get_config

# Set up constant test values
OWNER_ID = 12345
EMAIL_USERNAME = "testuser"
VANITY_NAME = "example.com"
STACKID = "notarealstackid"
CONFIG = {
    "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
    "DB_CLUSTER_ARN": "arn:aws:rds:region:account-id:cluster:cluster-id",
    "DATABASE_NAME": "test_db",
}


@pytest.fixture
def mock_rds_client():
    return MagicMock()


def test_register_workmail_stack_success(mock_rds_client):
    """Test successful execution of register_workmail_stack."""
    # Act
    register_workmail_stack(
        OWNER_ID, EMAIL_USERNAME, VANITY_NAME, STACKID, mock_rds_client, config=CONFIG
    )

    # Assert
    mock_rds_client.execute_statement.assert_called_once()
    args, kwargs = mock_rds_client.execute_statement.call_args

    assert kwargs["secretArn"] == CONFIG["DB_SECRET_ARN"]
    assert kwargs["resourceArn"] == CONFIG["DB_CLUSTER_ARN"]
    assert kwargs["database"] == CONFIG["DATABASE_NAME"]
    assert (
        kwargs["sql"]
        == """
        INSERT INTO workmail_stacks (ownerid, email_username, vanity_name, stackid)
        VALUES (:ownerid, :email_username, :vanity_name, :stack_id)
        """
    )
    assert kwargs["parameters"] == [
        {"name": "ownerid", "value": {"longValue": OWNER_ID}},
        {"name": "email_username", "value": {"stringValue": EMAIL_USERNAME}},
        {"name": "vanity_name", "value": {"stringValue": VANITY_NAME}},
        {"name": "stack_id", "value": {"stringValue": STACKID}},
    ]


def test_register_workmail_stack_client_error(mock_rds_client):
    """Test register_workmail_stack when ClientError is raised."""
    # Simulate ClientError
    mock_rds_client.execute_statement.side_effect = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="ExecuteStatement",
    )

    # Act & Assert
    with pytest.raises(ClientError) as excinfo:
        register_workmail_stack(
            OWNER_ID,
            EMAIL_USERNAME,
            VANITY_NAME,
            STACKID,
            mock_rds_client,
            config=CONFIG,
        )
    assert "Access Denied" in str(excinfo.value)
    mock_rds_client.execute_statement.assert_called_once()


def test_register_workmail_stack_botocore_error(mock_rds_client):
    """Test register_workmail_stack when BotoCoreError is raised."""
    # Simulate BotoCoreError
    mock_rds_client.execute_statement.side_effect = BotoCoreError()

    # Act & Assert
    with pytest.raises(BotoCoreError) as excinfo:
        register_workmail_stack(
            OWNER_ID,
            EMAIL_USERNAME,
            VANITY_NAME,
            STACKID,
            mock_rds_client,
            config=CONFIG,
        )
    assert "An unspecified error occurred" in str(excinfo.value)
    mock_rds_client.execute_statement.assert_called_once()


def test_register_workmail_stack_unexpected_error(mock_rds_client):
    """Test register_workmail_stack when an unexpected error is raised."""
    # Simulate unexpected error
    mock_rds_client.execute_statement.side_effect = Exception("Unexpected error")

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        register_workmail_stack(
            OWNER_ID,
            EMAIL_USERNAME,
            VANITY_NAME,
            STACKID,
            mock_rds_client,
            config=CONFIG,
        )
    assert "Unexpected error" in str(excinfo.value)
    mock_rds_client.execute_statement.assert_called_once()
