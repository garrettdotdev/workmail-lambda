# create_workmail_org_function/config.py
import os


def get_config():
    required_vars = ["WORKMAIL_STEPFUNCTION_ARN"]
    config = {}
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentError(
                f"Environment variable {var} is required but not set."
            )
        config[var] = value
    return config
