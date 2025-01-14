# tests/delete_workmail_org_function/unit/test_get_config.py
import unittest
import os
from unittest.mock import patch, MagicMock
from delete_workmail_org_function.app import get_config


class TestGetConfig(unittest.TestCase):

    @patch.dict(
        os.environ,
        {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:db-secret",
            "DB_CLUSTER_ARN": "arn:aws:rds:region:account-id:cluster:db-cluster",
            "DATABASE_NAME": "test_db",
            "SNS_BOUNCE_ARN": "arn:aws:sns:region:account-id:bounce",
            "SNS_COMPLAINT_ARN": "arn:aws:sns:region:account-id:complaint",
            "SNS_DELIVERY_ARN": "arn:aws:sns:region:account-id:delivery",
        },
    )
    def test_get_config_success(self):
        config = get_config()
        self.assertEqual(
            config["DB_SECRET_ARN"],
            "arn:aws:secretsmanager:region:account-id:secret:db-secret",
        )
        self.assertEqual(
            config["DB_CLUSTER_ARN"], "arn:aws:rds:region:account-id:cluster:db-cluster"
        )
        self.assertEqual(config["DATABASE_NAME"], "test_db")
        self.assertEqual(
            config["SNS_BOUNCE_ARN"], "arn:aws:sns:region:account-id:bounce"
        )
        self.assertEqual(
            config["SNS_COMPLAINT_ARN"], "arn:aws:sns:region:account-id:complaint"
        )
        self.assertEqual(
            config["SNS_DELIVERY_ARN"], "arn:aws:sns:region:account-id:delivery"
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_get_config_missing_env_vars(self):
        with self.assertRaises(EnvironmentError) as context:
            get_config()
        self.assertIn(
            "Environment variable DB_SECRET_ARN is required but not set.",
            str(context.exception),
        )

    @patch.dict(
        os.environ,
        {
            "DB_SECRET_ARN": "arn:aws:secretsmanager:region:account-id:secret:db-secret",
            "DB_CLUSTER_ARN": "arn:aws:rds:region:account-id:cluster:db-cluster",
            "DATABASE_NAME": "test_db",
            "SNS_BOUNCE_ARN": "arn:aws:sns:region:account-id:bounce",
            "SNS_COMPLAINT_ARN": "arn:aws:sns:region:account-id:complaint",
        },
        clear=True,
    )
    def test_get_config_partial_env_vars(self):
        with self.assertRaises(EnvironmentError) as context:
            get_config()
        self.assertIn(
            "Environment variable SNS_DELIVERY_ARN is required but not set.",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()
