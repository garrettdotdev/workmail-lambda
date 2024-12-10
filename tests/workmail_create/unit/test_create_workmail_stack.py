# tests/workmail_create/unit/test_create_workmail_stack.py
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError
from workmail_create.app import create_workmail_stack

# Set up constant test values
ORG_NAME = "example"
VANITY_NAME = "example.com"
EMAIL_USERNAME = "testuser"
DISPLAY_NAME = "Test User"
PASSWORD = "password123!"
FIRST_NAME = "Test"
LAST_NAME = "User"
STACK_ID = "arn:aws:cloudformation:region:account-id:stack/stack-name/guid"


@patch("workmail_create.app.boto3.client")
def test_create_workmail_stack_success(mock_boto_client):
    """Test successful execution of create_workmail_stack."""
    # Mock CloudFormation client
    mock_cf_client = MagicMock()
    mock_cf_client.create_stack.return_value = {"StackId": STACK_ID}
    mock_boto_client.return_value = mock_cf_client

    # Act
    stack_id = create_workmail_stack(
        ORG_NAME,
        VANITY_NAME,
        EMAIL_USERNAME,
        DISPLAY_NAME,
        PASSWORD,
        FIRST_NAME,
        LAST_NAME,
        mock_cf_client,
    )

    # Assert
    mock_cf_client.create_stack.assert_called_once()
    assert stack_id == STACK_ID


@patch("workmail_create.app.boto3.client")
def test_create_workmail_stack_client_error(mock_boto_client):
    """Test create_workmail_stack when ClientError is raised."""
    # Mock CloudFormation client
    mock_cf_client = MagicMock()
    mock_cf_client.create_stack.side_effect = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="CreateStack",
    )
    mock_boto_client.return_value = mock_cf_client

    # Act & Assert
    with pytest.raises(ClientError) as excinfo:
        create_workmail_stack(
            ORG_NAME,
            VANITY_NAME,
            EMAIL_USERNAME,
            DISPLAY_NAME,
            PASSWORD,
            FIRST_NAME,
            LAST_NAME,
            mock_cf_client,
        )
    assert "Access Denied" in str(excinfo.value)
    mock_cf_client.create_stack.assert_called_once()


@patch("workmail_create.app.boto3.client")
def test_create_workmail_stack_botocore_error(mock_boto_client):
    """Test create_workmail_stack when BotoCoreError is raised."""
    # Mock CloudFormation client
    mock_cf_client = MagicMock()
    mock_cf_client.create_stack.side_effect = BotoCoreError()
    mock_boto_client.return_value = mock_cf_client

    # Act & Assert
    with pytest.raises(BotoCoreError) as excinfo:
        create_workmail_stack(
            ORG_NAME,
            VANITY_NAME,
            EMAIL_USERNAME,
            DISPLAY_NAME,
            PASSWORD,
            FIRST_NAME,
            LAST_NAME,
            mock_cf_client,
        )
    assert "An unspecified error occurred" in str(excinfo.value)
    mock_cf_client.create_stack.assert_called_once()


@patch("workmail_create.app.boto3.client")
def test_create_workmail_stack_unexpected_error(mock_boto_client):
    """Test create_workmail_stack when an unexpected error is raised."""
    # Mock CloudFormation client
    mock_cf_client = MagicMock()
    mock_cf_client.create_stack.side_effect = Exception("Unexpected error")
    mock_boto_client.return_value = mock_cf_client

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        create_workmail_stack(
            ORG_NAME,
            VANITY_NAME,
            EMAIL_USERNAME,
            DISPLAY_NAME,
            PASSWORD,
            FIRST_NAME,
            LAST_NAME,
            mock_cf_client,
        )
    assert "Unexpected error" in str(excinfo.value)
    mock_cf_client.create_stack.assert_called_once()
