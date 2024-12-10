# tests/workmail_create/unit/test_add_contact_to_group.py
import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException
from workmail_create.app import add_contact_to_group

# Set up constant test values
CONTACT_ID = 12345
TAG_ID = 67890
CONFIG = {
    "KEAP_BASE_URL": "https://api.keap.com/",
    "KEAP_API_KEY": "test-api-key",
}


@patch("workmail_create.app.requests.post")
def test_add_contact_to_group_success(mock_post):
    """Test successful execution of add_contact_to_group."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_post.return_value = mock_response

    # Act
    response = add_contact_to_group(CONTACT_ID, TAG_ID, CONFIG)

    # Assert
    mock_post.assert_called_once_with(
        f"https://api.keap.com/contacts/{CONTACT_ID}/tags",
        headers={
            "Authorization": f"Bearer {CONFIG['KEAP_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={"tagIds": [TAG_ID]},
    )
    assert response == {"success": True}


@patch("workmail_create.app.requests.post")
def test_add_contact_to_group_request_exception(mock_post):
    """Test add_contact_to_group when RequestException is raised."""
    # Simulate RequestException
    mock_post.side_effect = RequestException("Request failed")

    # Act & Assert
    with pytest.raises(RequestException) as excinfo:
        add_contact_to_group(CONTACT_ID, TAG_ID, CONFIG)
    assert "Request failed" in str(excinfo.value)
    mock_post.assert_called_once()


@patch("workmail_create.app.requests.post")
def test_add_contact_to_group_unexpected_error(mock_post):
    """Test add_contact_to_group when an unexpected error is raised."""
    # Simulate unexpected error
    mock_post.side_effect = Exception("Unexpected error")

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        add_contact_to_group(CONTACT_ID, TAG_ID, CONFIG)
    assert "Unexpected error" in str(excinfo.value)
    mock_post.assert_called_once()
