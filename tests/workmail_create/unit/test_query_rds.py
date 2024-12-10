# tests/workmail_create/unit/test_query_rds.py
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError
from workmail_create.app import query_rds

# Set up constant test values
CONTACT_ID = 12345
APPNAME = "test_app"
FIRST_NAME = "John"
LAST_NAME = "Doe"
CONFIG = {
    "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:secret-id",
    "DB_CLUSTER_ARN": "arn:aws:rds:region:account-id:cluster:cluster-id",
    "DATABASE_NAME": "test_db",
}


@pytest.fixture
def mock_rds_client():
    return MagicMock()


def test_query_rds_success(mock_rds_client):
    """Test successful execution of query_rds."""
    # Mock RDS client response
    mock_rds_client.execute_statement.return_value = {
        "records": [[{"stringValue": FIRST_NAME}, {"stringValue": LAST_NAME}]]
    }

    # Act
    first_name, last_name = query_rds(CONTACT_ID, APPNAME, mock_rds_client, CONFIG)

    # Assert
    assert first_name == FIRST_NAME
    assert last_name == LAST_NAME
    mock_rds_client.execute_statement.assert_called_once()


def test_query_rds_no_records(mock_rds_client):
    """Test query_rds when no records are found."""
    # Mock RDS client response with no records
    mock_rds_client.execute_statement.return_value = {"records": []}

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        query_rds(CONTACT_ID, APPNAME, mock_rds_client, CONFIG)
    assert "No customer found" in str(excinfo.value)
    mock_rds_client.execute_statement.assert_called_once()


def test_query_rds_client_error(mock_rds_client):
    """Test query_rds when ClientError is raised."""
    # Simulate ClientError
    mock_rds_client.execute_statement.side_effect = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="ExecuteStatement",
    )

    # Act & Assert
    with pytest.raises(ClientError) as excinfo:
        query_rds(CONTACT_ID, APPNAME, mock_rds_client, CONFIG)
    assert "Access Denied" in str(excinfo.value)
    mock_rds_client.execute_statement.assert_called_once()


def test_query_rds_botocore_error(mock_rds_client):
    """Test query_rds when BotoCoreError is raised."""
    # Simulate BotoCoreError
    mock_rds_client.execute_statement.side_effect = BotoCoreError()

    # Act & Assert
    with pytest.raises(BotoCoreError) as excinfo:
        query_rds(CONTACT_ID, APPNAME, mock_rds_client, CONFIG)
    assert "An unspecified error occurred" in str(excinfo.value)
    mock_rds_client.execute_statement.assert_called_once()


def test_query_rds_unexpected_error(mock_rds_client):
    """Test query_rds when an unexpected error is raised."""
    # Simulate unexpected error
    mock_rds_client.execute_statement.side_effect = Exception("Unexpected error")

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        query_rds(CONTACT_ID, APPNAME, mock_rds_client, CONFIG)
    assert "Unexpected error" in str(excinfo.value)
    mock_rds_client.execute_statement.assert_called_once()
