# workmail_create/config.py
import os


def get_env_variable(key, default=None, env=os.environ):
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} is required")
    return value


def get_config(env=os.environ):
    return {
        "DB_SECRET_ARN": get_env_variable("DB_SECRET_ARN", env=env),
        "DB_CLUSTER_ARN": get_env_variable("DB_CLUSTER_ARN", env=env),
        "DATABASE_NAME": get_env_variable("DATABASE_NAME", env=env),
        "ORGANIZATION_ID": get_env_variable("ORGANIZATION_ID", env=env),
        "KEAP_BASE_URL": get_env_variable("KEAP_BASE_URL", env=env),
        "KEAP_API_KEY": get_env_variable("KEAP_API_KEY", env=env),
        "KEAP_TAG": get_env_variable("KEAP_TAG", env=env),
        "SNS_BOUNCE_ARN": get_env_variable("SNS_BOUNCE_ARN", env=env),
        "SNS_COMPLAINT_ARN": get_env_variable("SNS_COMPLAINT_ARN", env=env),
        "SNS_DELIVERY_ARN": get_env_variable("SNS_DELIVERY_ARN", env=env),
    }
