# tests/create_workmail_org_function/unit/test_prepare_keap_updates.py
import unittest
from unittest.mock import patch, MagicMock
from create_workmail_org_function.app import prepare_keap_updates


class TestPrepareKeapUpdates(unittest.TestCase):

    def test_prepare_keap_updates_success(self):
        # Arrange
        dns_records = [
            {
                "Type": "MX",
                "Hostname": "example.com.",
                "Value": "10 inbound-smtp.us-east-1.amazonaws.com.",
            },
            {
                "Type": "TXT",
                "Hostname": "_amazonses.example.com",
                "Value": "value2",
            },
            {
                "Type": "CNAME",
                "Hostname": "autodiscover.example.com",
                "Value": "value3",
            },
            {
                "Type": "CNAME",
                "Hostname": "test4._domainkey.example.com",
                "Value": "value4",
            },
            {
                "Type": "CNAME",
                "Hostname": "test5._domainkey.example.com",
                "Value": "value5",
            },
            {
                "Type": "CNAME",
                "Hostname": "test6._domainkey.example.com",
                "Value": "value6",
            },
            {
                "Type": "TXT",
                "Hostname": "example.com.",
                "Value": "v=spf1 include:amazonses.com ~all",
            },
            {
                "Type": "TXT",
                "Hostname": "_dmarc.example.com",
                "Value": "v=DMARC1;p=quarantine;pct=100;fo=1",
            },
        ]

        # Act
        result = prepare_keap_updates(dns_records)

        # Assert
        expected_result = {
            "API1": "example.com.",
            "API2": "value2",
            "API3": "value4",
            "API4": "value5",
            "API5": "value6",
        }
        self.assertEqual(result, expected_result)

    def test_prepare_keap_updates_partial_success(self):
        # Arrange
        dns_records = [
            {
                "Type": "TXT",
                "Hostname": "test1._amazonses.example.com",
                "Value": "value1",
            },
            {
                "Type": "CNAME",
                "Hostname": "test2._domainkey.example.com",
                "Value": "value2",
            },
        ]

        # Act
        result = prepare_keap_updates(dns_records)

        # Assert
        expected_result = {
            "API2": "value1",
            "API3": "value2",
        }
        self.assertEqual(result, expected_result)

    def test_prepare_keap_updates_no_matching_records(self):
        # Arrange
        dns_records = []

        # Act
        result = prepare_keap_updates(dns_records)

        # Assert
        expected_result = {}
        self.assertEqual(expected_result, result)

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
