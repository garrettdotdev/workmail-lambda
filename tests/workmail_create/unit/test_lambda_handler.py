# tests/workmail_create/unit/test_lambda_handler.py
import pytest
import json
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError
from workmail_create.app import lambda_handler

# Set up constant test values
EVENT = {
    "body": json.dumps(
        {
            "contact_id": 12345,
            "appname": "testapp",
            "email_username": "testuser",
            "vanity_name": "example.com",
        }
    )
}
CONTEXT = {}
CONFIG = {
    "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
    "DB_CLUSTER_ARN": "arn:aws:rds:region:account-id:cluster:cluster-id",
    "DATABASE_NAME": "test_db",
    "SNS_BOUNCE_ARN": "arn:aws:sns:region:account-id:bounce-topic",
    "SNS_COMPLAINT_ARN": "arn:aws:sns:region:account-id:complaint-topic",
    "SNS_DELIVERY_ARN": "arn:aws:sns:region:account-id:delivery-topic",
    "KEAP_BASE_URL": "https://api.keap.com/",
    "KEAP_API_KEY": "test-api-key",
    "KEAP_TAG": 67890,
    "ORGANIZATION_ID": "org-id",
}


@patch("workmail_create.app.get_config", return_value=CONFIG)
@patch("workmail_create.app.get_aws_clients")
@patch("workmail_create.app.query_rds", return_value=("Test", "User"))
@patch("workmail_create.app.generate_random_password", return_value="password123!")
@patch("workmail_create.app.create_workmail_stack", return_value="stack-id")
@patch("workmail_create.app.register_workmail_stack")
@patch("workmail_create.app.set_ses_notifications")
@patch("workmail_create.app.get_dns_records", return_value=[])
@patch("workmail_create.app.update_contact")
@patch("workmail_create.app.add_contact_to_group")
def test_lambda_handler_success(
    mock_add_contact_to_group,
    mock_update_contact,
    mock_get_dns_records,
    mock_set_ses_notifications,
    mock_register_workmail_stack,
    mock_create_workmail_stack,
    mock_generate_random_password,
    mock_query_rds,
    mock_get_aws_clients,
    mock_get_config,
):
    """Test successful execution of lambda_handler."""
    # Mock AWS clients
    mock_aws_clients = {
        "rds_client": MagicMock(),
        "cloudformation_client": MagicMock(),
        "ses_client": MagicMock(),
        "workmail_client": MagicMock(),
    }
    mock_get_aws_clients.return_value = mock_aws_clients

    # Act
    response = lambda_handler(EVENT, CONTEXT)

    # Assert
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "message": "WorkMail organization and user creation initiated.",
        "stackId": "stack-id",
        "email": "testuser@example.com",
    }


@patch("workmail_create.app.get_config", return_value=CONFIG)
@patch("workmail_create.app.get_aws_clients")
@patch(
    "workmail_create.app.query_rds",
    side_effect=ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="ExecuteStatement",
    ),
)
def test_lambda_handler_client_error(
    mock_query_rds, mock_get_aws_clients, mock_get_config
):
    """Test lambda_handler when ClientError is raised."""
    # Mock AWS clients
    mock_aws_clients = {
        "rds_client": MagicMock(),
        "cloudformation_client": MagicMock(),
        "ses_client": MagicMock(),
        "workmail_client": MagicMock(),
    }
    mock_get_aws_clients.return_value = mock_aws_clients

    # Act
    response = lambda_handler(EVENT, CONTEXT)

    # Assert
    assert response["statusCode"] == 500
    assert "Access Denied" in json.loads(response["body"])["error"]


@patch("workmail_create.app.get_config", return_value=CONFIG)
@patch("workmail_create.app.get_aws_clients")
@patch("workmail_create.app.query_rds", side_effect=BotoCoreError())
def test_lambda_handler_botocore_error(
    mock_query_rds, mock_get_aws_clients, mock_get_config
):
    """Test lambda_handler when BotoCoreError is raised."""
    # Mock AWS clients
    mock_aws_clients = {
        "rds_client": MagicMock(),
        "cloudformation_client": MagicMock(),
        "ses_client": MagicMock(),
        "workmail_client": MagicMock(),
    }
    mock_get_aws_clients.return_value = mock_aws_clients

    # Act
    response = lambda_handler(EVENT, CONTEXT)

    # Assert
    assert response["statusCode"] == 500
    assert "An unspecified error occurred" in json.loads(response["body"])["error"]


@patch("workmail_create.app.get_config", return_value=CONFIG)
@patch("workmail_create.app.get_aws_clients")
@patch("workmail_create.app.query_rds", side_effect=ValueError("No customer found"))
def test_lambda_handler_value_error(
    mock_query_rds, mock_get_aws_clients, mock_get_config
):
    """Test lambda_handler when ValueError is raised."""
    # Mock AWS clients
    mock_aws_clients = {
        "rds_client": MagicMock(),
        "cloudformation_client": MagicMock(),
        "ses_client": MagicMock(),
        "workmail_client": MagicMock(),
    }
    mock_get_aws_clients.return_value = mock_aws_clients

    # Act
    response = lambda_handler(EVENT, CONTEXT)

    # Assert
    assert response["statusCode"] == 400
    assert "No customer found" in json.loads(response["body"])["error"]


@patch("workmail_create.app.get_config", return_value=CONFIG)
@patch("workmail_create.app.get_aws_clients")
@patch("workmail_create.app.query_rds", side_effect=Exception("Unexpected error"))
def test_lambda_handler_unexpected_error(
    mock_query_rds, mock_get_aws_clients, mock_get_config
):
    """Test lambda_handler when an unexpected error is raised."""
    # Mock AWS clients
    mock_aws_clients = {
        "rds_client": MagicMock(),
        "cloudformation_client": MagicMock(),
        "ses_client": MagicMock(),
        "workmail_client": MagicMock(),
    }
    mock_get_aws_clients.return_value = mock_aws_clients

    # Act
    response = lambda_handler(EVENT, CONTEXT)

    # Assert
    assert response["statusCode"] == 500
    assert "Unexpected error" in json.loads(response["body"])["error"]
