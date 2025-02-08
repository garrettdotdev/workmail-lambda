import json
import logging
import os

from workmail_common.utils import get_aws_client, keap_contact_create_note_via_proxy

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_config():
    required_vars = [
        "AWS_ACCOUNT_ID",
        "KEAP_API_KEY_SECRET_NAME",
        "PROXY_ENDPOINT",
        "PROXY_ENDPOINT_HOST",
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


def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        contact_id = event["contact_id"]
        domain_name = event["vanity_name"]
        # configuration_set = f"{organization_id}-config-set"

        config = get_config()

        # Create IAM User
        logger.info(f"Attempting to create IAM User for domain {domain_name}")
        iam = get_aws_client("iam")
        iam_user_name = f"workmail_{domain_name}"

        create_user_response = iam.create_user(UserName=iam_user_name)
        logger.info(f"IAM User created: {create_user_response['User']['UserName']}")

        # Define the SES policy with dynamic ARNs
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowSESSendEmail",
                    "Effect": "Allow",
                    "Action": ["ses:SendEmail", "ses:SendRawEmail"],
                    "Resource": [
                        # f"arn:aws:ses:us-east-1:{os.getenv('AWS_ACCOUNT_ID')}:configuration-set/{configuration_set}",
                        f"arn:aws:ses:us-east-1:{os.getenv('AWS_ACCOUNT_ID')}:identity/{domain_name}",
                    ],
                },
                {
                    "Sid": "AllowSESListIdentities",
                    "Effect": "Allow",
                    "Action": "ses:ListIdentities",
                    "Resource": "*",
                },
            ],
        }

        logger.info(f"Attempting to attach policy to user: {iam_user_name}")
        policy_response = iam.put_user_policy(
            UserName=iam_user_name,
            PolicyName=f"workmail_{domain_name}_fluentsmtp_policy",
            PolicyDocument=json.dumps(policy_document),
        )
        logger.info(f"Policy attached to user: {policy_response}")

        # Generate and return API key for IAM user
        logger.info(f"Attempting to create access key for user: {iam_user_name}")
        access_key = iam.create_access_key(UserName=iam_user_name)
        api_key = access_key["AccessKey"]["AccessKeyId"]
        secret_key = access_key["AccessKey"]["SecretAccessKey"]
        logger.info(f"Access key created for user: {iam_user_name}")

        keap_contact_create_note_via_proxy(
            contact_id,
            "IAM User Info",
            {
                "IAM User Name": iam_user_name,
                "API Key": api_key,
                "Secret Key": secret_key,
            },
            config,
        )

        return {
            "iamUserName": iam_user_name,
            "apiKey": api_key,
            "secretKey": secret_key,
        }

    except Exception as e:
        logger.exception(str(e))
        raise e
