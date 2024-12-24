import unittest
from unittest.mock import patch, MagicMock
from create_workmail_org_function.app import add_contact_to_group


class TestAddContactToGroup(unittest.TestCase):

    @patch("create_workmail_org_function.app.get_secret_value")
    @patch("create_workmail_org_function.app.requests.post")
    def test_add_contact_to_group_success(self, mock_post, mock_get_secret_value):
        # Arrange
        contact_id = 123
        tag_id = 456
        config = {
            "KEAP_BASE_URL": "https://api.keap.com/",
            "KEAP_API_KEY_SECRET_NAME": "keap_api_key_secret",
        }
        mock_get_secret_value.return_value = "fake_keap_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        # Act
        result = add_contact_to_group(contact_id, tag_id, config)

        # Assert
        self.assertEqual(result, {"success": True})
        mock_get_secret_value.assert_called_once_with("keap_api_key_secret")
        mock_post.assert_called_once_with(
            "https://api.keap.com/contacts/123/tags",
            headers={
                "Authorization": "Bearer fake_keap_token",
                "Content-Type": "application/json",
            },
            json={"tagIds": [456]},
        )

    @patch("create_workmail_org_function.app.get_secret_value")
    @patch("create_workmail_org_function.app.requests.post")
    def test_add_contact_to_group_failure(self, mock_post, mock_get_secret_value):
        # Arrange
        contact_id = 123
        tag_id = 456
        config = {
            "KEAP_BASE_URL": "https://api.keap.com/",
            "KEAP_API_KEY_SECRET_NAME": "keap_api_key_secret",
        }
        mock_get_secret_value.return_value = "fake_keap_token"
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            add_contact_to_group(contact_id, tag_id, config)

        self.assertEqual(
            str(context.exception), "Failed to add contact 123 to tag 456: Bad Request"
        )
        mock_get_secret_value.assert_called_once_with("keap_api_key_secret")
        mock_post.assert_called_once_with(
            "https://api.keap.com/contacts/123/tags",
            headers={
                "Authorization": "Bearer fake_keap_token",
                "Content-Type": "application/json",
            },
            json={"tagIds": [456]},
        )


if __name__ == "__main__":
    unittest.main()
