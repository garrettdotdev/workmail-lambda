import os


def get_config():
    required_vars = ["DB_SECRET_ARN", "DB_CLUSTER_ARN", "DATABASE_NAME"]
    config = {}
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            raise EnvironmentError(
                f"Environment variable {var} is required but not set."
            )
        config[var] = value
    return config
