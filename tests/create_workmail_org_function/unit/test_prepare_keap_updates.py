# tests/create_workmail_org_function/unit/test_prepare_keap_updates.py
import unittest
from unittest.mock import patch, MagicMock
from create_workmail_org_function.app import prepare_keap_updates


class TestPrepareKeapUpdates(unittest.TestCase):

    def test_prepare_keap_updates_success(self):
        # Arrange
        dns_records = [
            {"Hostname": "test1._amazonses.example.com", "Value": "value1"},
            {"Hostname": "test2._domainkey.example.com", "Value": "value2"},
            {"Hostname": "test3._domainkey.example.com", "Value": "value3"},
            {"Hostname": "test4._domainkey.example.com", "Value": "value4"},
        ]

        # Act
        result = prepare_keap_updates(dns_records)

        # Assert
        expected_result = {
            "API1": "value1",
            "API2": "value2",
            "API3": "value3",
            "API4": "value4",
        }
        self.assertEqual(result, expected_result)

    def test_prepare_keap_updates_partial_success(self):
        # Arrange
        dns_records = [
            {"Hostname": "test1._amazonses.example.com", "Value": "value1"},
            {"Hostname": "test2._domainkey.example.com", "Value": "value2"},
        ]

        # Act
        result = prepare_keap_updates(dns_records)

        # Assert
        expected_result = {
            "API1": "value1",
            "API2": "value2",
        }
        self.assertEqual(result, expected_result)

    def test_prepare_keap_updates_no_matching_records(self):
        # Arrange
        dns_records = [
            {"Hostname": "test1.example.com", "Value": "value1"},
            {"Hostname": "test2.example.com", "Value": "value2"},
        ]

        # Act
        result = prepare_keap_updates(dns_records)

        # Assert
        expected_result = {}
        self.assertEqual(result, expected_result)

    def test_prepare_keap_updates_exception(self):
        # Arrange
        dns_records = [
            {"Hostname": "test1._amazonses.example.com", "Value": "value1"},
            {"Hostname": "test2._domainkey.example.com", "Value": "value2"},
        ]

        # Act & Assert
        with self.assertRaises(Exception):
            with patch("create_workmail_org_function.app.logger") as mock_logger:
                mock_logger.info.side_effect = Exception("Test exception")
                prepare_keap_updates(dns_records)


if __name__ == "__main__":
    unittest.main()
