# tests/workmail_create/unit/test_update_contact.py
import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException
from workmail_create.app import update_contact

# Set up constant test values
CONTACT_ID = 12345
CUSTOM_FIELDS = {"field1": "value1", "field2": "value2"}
CONFIG = {
    "KEAP_BASE_URL": "https://api.keap.com/",
    "KEAP_API_KEY": "test-api-key",
}


@patch("workmail_create.app.requests.patch")
def test_update_contact_success(mock_patch):
    """Test successful execution of update_contact."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_patch.return_value = mock_response

    # Act
    response = update_contact(CONTACT_ID, CUSTOM_FIELDS, CONFIG)

    # Assert
    mock_patch.assert_called_once_with(
        f"https://api.keap.com/contacts/{CONTACT_ID}",
        headers={
            "Authorization": f"Bearer {CONFIG['KEAP_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={"custom_fields": CUSTOM_FIELDS},
    )
    assert response == {"success": True}


@patch("workmail_create.app.requests.patch")
def test_update_contact_request_exception(mock_patch):
    """Test update_contact when RequestException is raised."""
    # Simulate RequestException
    mock_patch.side_effect = RequestException("Request failed")

    # Act & Assert
    with pytest.raises(RequestException) as excinfo:
        update_contact(CONTACT_ID, CUSTOM_FIELDS, CONFIG)
    assert "Request failed" in str(excinfo.value)
    mock_patch.assert_called_once()


@patch("workmail_create.app.requests.patch")
def test_update_contact_unexpected_error(mock_patch):
    """Test update_contact when an unexpected error is raised."""
    # Simulate unexpected error
    mock_patch.side_effect = Exception("Unexpected error")

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        update_contact(CONTACT_ID, CUSTOM_FIELDS, CONFIG)
    assert "Unexpected error" in str(excinfo.value)
    mock_patch.assert_called_once()
