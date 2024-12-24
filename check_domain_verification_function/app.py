# check_domain_verification_function/app.py
import logging
import os
from workmail_common.utils import (
    handle_error,
    get_aws_client,
    validate,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {event}")
        pwd = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(pwd, "schemas/input_schema.json")
        if not validate(event, schema_path):
            raise Exception("Input validation failed")

        organization_id = event["organization_id"]
        vanity_name = event["vanity_name"]

        logger.info(
            f"Checking domain verification for {vanity_name} (orgid: {organization_id})"
        )

        workmail_client = get_aws_client("workmail")

        mail_domain_response = workmail_client.describe_mail_domain(
            OrganizationId=organization_id, DomainName=vanity_name
        )

        expected_keys = {"OwnershipVerificationStatus", "DkimVerificationStatus"}
        if not isinstance(mail_domain_response, dict) or not expected_keys.issubset(
            mail_domain_response.keys()
        ):
            logger.error(f"Unexpected response from WorkMail: {mail_domain_response}")
            raise Exception("Unexpected response from WorkMail")

        ownership_verification_status = mail_domain_response[
            "OwnershipVerificationStatus"
        ]
        dkim_verification_status = mail_domain_response["DkimVerificationStatus"]
        if (
            ownership_verification_status != "VERIFIED"
            or dkim_verification_status != "VERIFIED"
        ):
            logger.warning(
                f"Domain not verified: Ownership = {ownership_verification_status}, Dkim = {dkim_verification_status}"
            )
            return {"domainVerification": False}

        logger.info(f"Domain is verified")
        return {"domainVerification": True}

    except Exception as e:
        return handle_error(e)
