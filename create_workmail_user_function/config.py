# create_workmail_org_function/config.py
import os


def get_config():
    required_vars = [
        "DB_SECRET_ARN",
        "DB_CLUSTER_ARN",
        "DATABASE_NAME",
        "SNS_BOUNCE_ARN",
        "SNS_COMPLAINT_ARN",
        "SNS_DELIVERY_ARN",
        "KEAP_BASE_URL",
        "KEAP_API_KEY_SECRET_NAME",
        "KEAP_TAG",
    ]
    config = {}
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentError(
                f"Environment variable {var} is required but not set."
            )
        config[var] = value
    return config
