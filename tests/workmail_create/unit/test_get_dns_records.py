# tests/workmail_create/unit/test_get_dns_records.py
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from workmail_create.app import get_dns_records

# Set up constant test values
DOMAIN_NAME = "example.com"
ORGANIZATION_ID = "example-organization-id"
DKIM_TOKENS = ["token1", "token2", "token3"]
WORKMAIL_DNS_RECORDS = [
    {"Type": "MX", "Name": "example.com", "Value": "10 mail.example.com"},
    {
        "Type": "CNAME",
        "Name": "autodiscover.example.com",
        "Value": "autodiscover.mail.example.com",
    },
]


@patch("workmail_create.app.get_config")
@patch("workmail_create.app.get_aws_clients")
def test_get_dns_records_success(mock_get_aws_clients, mock_get_config):
    """Test that get_dns_records successfully fetches DNS records."""

    # Mock configuration
    mock_get_config.return_value = {"ORGANIZATION_ID": ORGANIZATION_ID}

    # Mock AWS clients
    mock_ses_client = MagicMock()
    mock_workmail_client = MagicMock()
    mock_get_aws_clients.return_value = {
        "ses_client": mock_ses_client,
        "workmail_client": mock_workmail_client,
    }

    # Mock SES client responses
    mock_ses_client.get_identity_dkim_attributes.return_value = {
        "DkimAttributes": {DOMAIN_NAME: {"DkimTokens": DKIM_TOKENS}}
    }

    # Mock WorkMail client responses
    mock_workmail_client.describe_mail_domain.return_value = {
        "DNSRecords": WORKMAIL_DNS_RECORDS
    }

    # Act
    dns_records = get_dns_records(
        DOMAIN_NAME, mock_ses_client, mock_workmail_client, mock_get_config.return_value
    )

    # Assert
    expected_records = [
        {
            "Type": "CNAME",
            "Name": f"{token}._domainkey.{DOMAIN_NAME}",
            "Value": f"{token}.dkim.amazonses.com",
        }
        for token in DKIM_TOKENS
    ]
    expected_records.append(
        {
            "Type": "TXT",
            "Name": DOMAIN_NAME,
            "Value": '"v=spf1 include:amazonses.com ~all"',
        }
    )
    expected_records.append(
        {"Type": "TXT", "Name": f"_dmarc.{DOMAIN_NAME}", "Value": "v=DMARC1;p=none;"}
    )
    expected_records.extend(WORKMAIL_DNS_RECORDS)

    assert dns_records == expected_records


@patch("workmail_create.app.get_config")
@patch("workmail_create.app.get_aws_clients")
def test_get_dns_records_ses_client_error(mock_get_aws_clients, mock_get_config):
    """Test that get_dns_records raises an exception when SES client fails."""

    # Mock configuration
    mock_get_config.return_value = {"ORGANIZATION_ID": ORGANIZATION_ID}

    # Mock AWS clients
    mock_ses_client = MagicMock()
    mock_workmail_client = MagicMock()
    mock_get_aws_clients.return_value = {
        "ses_client": mock_ses_client,
        "workmail_client": mock_workmail_client,
    }

    # Simulate an error from the SES client
    mock_ses_client.get_identity_dkim_attributes.side_effect = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="GetIdentityDkimAttributes",
    )

    # Act & Assert
    with pytest.raises(ClientError) as excinfo:
        get_dns_records(
            DOMAIN_NAME,
            mock_ses_client,
            mock_workmail_client,
            mock_get_config.return_value,
        )

    assert "Access Denied" in str(excinfo.value)


@patch("workmail_create.app.get_config")
@patch("workmail_create.app.get_aws_clients")
def test_get_dns_records_workmail_client_error(mock_get_aws_clients, mock_get_config):
    """Test that get_dns_records raises an exception when WorkMail client fails."""

    # Mock configuration
    mock_get_config.return_value = {"ORGANIZATION_ID": ORGANIZATION_ID}

    # Mock AWS clients
    mock_ses_client = MagicMock()
    mock_workmail_client = MagicMock()
    mock_get_aws_clients.return_value = {
        "ses_client": mock_ses_client,
        "workmail_client": mock_workmail_client,
    }

    # Mock SES client responses
    mock_ses_client.get_identity_dkim_attributes.return_value = {
        "DkimAttributes": {DOMAIN_NAME: {"DkimTokens": DKIM_TOKENS}}
    }

    # Simulate an error from the WorkMail client
    mock_workmail_client.describe_mail_domain.side_effect = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="DescribeMailDomain",
    )

    # Act & Assert
    with pytest.raises(ClientError) as excinfo:
        get_dns_records(
            DOMAIN_NAME,
            mock_ses_client,
            mock_workmail_client,
            mock_get_config.return_value,
        )

    assert "Access Denied" in str(excinfo.value)


@patch("workmail_create.app.get_config")
@patch("workmail_create.app.get_aws_clients")
def test_get_dns_records_no_dkim_tokens(mock_get_aws_clients, mock_get_config):
    """Test that get_dns_records handles the case with no DKIM tokens."""

    # Mock configuration
    mock_get_config.return_value = {"ORGANIZATION_ID": ORGANIZATION_ID}

    # Mock AWS clients
    mock_ses_client = MagicMock()
    mock_workmail_client = MagicMock()
    mock_get_aws_clients.return_value = {
        "ses_client": mock_ses_client,
        "workmail_client": mock_workmail_client,
    }

    # Mock SES client responses with no DKIM tokens
    mock_ses_client.get_identity_dkim_attributes.return_value = {
        "DkimAttributes": {DOMAIN_NAME: {"DkimTokens": []}}
    }

    # Mock WorkMail client responses
    mock_workmail_client.describe_mail_domain.return_value = {
        "DNSRecords": WORKMAIL_DNS_RECORDS
    }

    # Act
    dns_records = get_dns_records(
        DOMAIN_NAME, mock_ses_client, mock_workmail_client, mock_get_config.return_value
    )

    # Assert
    expected_records = [
        {
            "Type": "TXT",
            "Name": DOMAIN_NAME,
            "Value": '"v=spf1 include:amazonses.com ~all"',
        }
    ]
    expected_records.append(
        {"Type": "TXT", "Name": f"_dmarc.{DOMAIN_NAME}", "Value": "v=DMARC1;p=none;"}
    )
    expected_records.extend(WORKMAIL_DNS_RECORDS)

    assert dns_records == expected_records
