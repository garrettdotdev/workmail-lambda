# workmail_create/app.py
import boto3
import json
import random
import string
import tldextract
import os
import requests
import logging
from botocore.exceptions import ClientError, BotoCoreError
from jsonschema import validate
from typing import Dict, Any, List, Tuple
from workmail_create.config import get_config
from workmail_common.utils import load_schema, handle_error

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_contact_to_group(
    contact_id: int, tag_id: int, config: Dict[str, str]
) -> Dict[str, Any]:
    """Add contact to a group."""
    try:
        keap_base_url = config["KEAP_BASE_URL"]
        keap_token = config["KEAP_API_KEY"]
        url = f"{keap_base_url}contacts/{contact_id}/tags"
        headers = {
            "Authorization": f"Bearer {keap_token}",
            "Content-Type": "application/json",
        }
        payload = {"tagIds": [tag_id]}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise ValueError(
                f"Failed to add contact {contact_id} to tag {tag_id}: {response.text}"
            )
        logger.info(f"Added contact {contact_id} to tag {tag_id}")
        return response.json()
    except Exception as e:
        raise


def create_workmail_stack(
    org_name: str,
    vanity_name: str,
    email_username: str,
    display_name: str,
    password: str,
    first_name: str,
    last_name: str,
    cloudformation_client: Any,
) -> str:
    """Create a WorkMail stack using CloudFormation."""
    try:
        parameters = [
            {"ParameterKey": "OrganizationName", "ParameterValue": org_name},
            {"ParameterKey": "DomainName", "ParameterValue": vanity_name},
            {"ParameterKey": "UserName", "ParameterValue": email_username},
            {"ParameterKey": "DisplayName", "ParameterValue": display_name},
            {"ParameterKey": "Password", "ParameterValue": password},
            {"ParameterKey": "FirstName", "ParameterValue": first_name},
            {"ParameterKey": "LastName", "ParameterValue": last_name},
        ]

        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(
            current_dir, "resources/workmail_create_template.yaml"
        )
        with open(template_path, "r") as file:
            response = cloudformation_client.create_stack(
                StackName=f"workmail-{org_name}",
                TemplateBody=file.read(),
                Parameters=parameters,
                Capabilities=["CAPABILITY_NAMED_IAM"],
            )
        return response["StackId"]
    except Exception as e:
        raise


def generate_random_password(length: int = 12) -> str:
    """Generate a random password."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choice(characters) for _ in range(length))


def get_aws_clients() -> Dict[str, Any]:
    return {
        "rds_client": boto3.client("rds-data"),
        "cloudformation_client": boto3.client("cloudformation"),
        "ses_client": boto3.client("ses"),
        "workmail_client": boto3.client("workmail"),
    }


def get_dns_records(
    domain_name: str, ses_client: Any, workmail_client: Any, config: Dict[str, str]
) -> List[Dict[str, str]]:
    """Get DNS records for a domain."""
    dns_records = []
    try:
        dkim_response = ses_client.get_identity_dkim_attributes(
            Identities=[domain_name]
        )
        dkim_tokens = (
            dkim_response["DkimAttributes"].get(domain_name, {}).get("DkimTokens", [])
        )
        for token in dkim_tokens:
            dns_records.append(
                {
                    "Type": "CNAME",
                    "Name": f"{token}._domainkey.{domain_name}",
                    "Value": f"{token}.dkim.amazonses.com",
                }
            )
        dns_records.append(
            {
                "Type": "TXT",
                "Name": domain_name,
                "Value": '"v=spf1 include:amazonses.com ~all"',
            }
        )
        dns_records.append(
            {
                "Type": "TXT",
                "Name": f"_dmarc.{domain_name}",
                "Value": "v=DMARC1;p=none;",
            }
        )
        organization_id = config["ORGANIZATION_ID"]
        workmail_response = workmail_client.describe_mail_domain(
            OrganizationId=organization_id, DomainName=domain_name
        )
        for record in workmail_response.get("DNSRecords", []):
            dns_records.append(
                {
                    "Type": record["Type"],
                    "Name": record["Name"],
                    "Value": record["Value"],
                }
            )
    except Exception as e:
        raise
    return dns_records


def query_rds(
    contact_id: int, appname: str, rds_client: Any, config: Dict[str, str]
) -> Tuple[str, str]:
    """Query RDS for customer information."""
    try:
        db_secret_arn = config["DB_SECRET_ARN"]
        db_cluster_arn = config["DB_CLUSTER_ARN"]
        database_name = config["DATABASE_NAME"]
        sql = """
        SELECT ownerfirstname, ownerlastname
        FROM app
        WHERE ownerid = :contact_id AND appname = :appname
        LIMIT 1
        """
        response = rds_client.execute_statement(
            secretArn=db_secret_arn,
            resourceArn=db_cluster_arn,
            sql=sql,
            database=database_name,
            parameters=[
                {"name": "contact_id", "value": {"longValue": contact_id}},
                {"name": "appname", "value": {"stringValue": appname}},
            ],
        )
        if not response["records"]:
            raise ValueError(
                f"No customer found with contact_id={contact_id} and appname={appname}"
            )
        first_name = response["records"][0][0]["stringValue"]
        last_name = response["records"][0][1]["stringValue"]
        return first_name, last_name
    except Exception as e:
        raise


def register_workmail_stack(
    ownerid: int,
    email_username: str,
    vanity_name: str,
    stack_id: str,
    rds_client: Any,
    config: Dict[str, str],
) -> None:
    """Register a WorkMail stack in the database."""
    try:
        db_secret_arn = config["DB_SECRET_ARN"]
        db_cluster_arn = config["DB_CLUSTER_ARN"]
        database_name = config["DATABASE_NAME"]
        sql = """
        INSERT INTO workmail_stacks (ownerid, email_username, vanity_name, stackid)
        VALUES (:ownerid, :email_username, :vanity_name, :stack_id)
        """
        rds_client.execute_statement(
            secretArn=db_secret_arn,
            resourceArn=db_cluster_arn,
            sql=sql,
            database=database_name,
            parameters=[
                {"name": "ownerid", "value": {"longValue": ownerid}},
                {"name": "email_username", "value": {"stringValue": email_username}},
                {"name": "vanity_name", "value": {"stringValue": vanity_name}},
                {"name": "stack_id", "value": {"stringValue": stack_id}},
            ],
        )
    except Exception as e:
        raise


def set_ses_notifications(
    identity: str, ses_client: Any, config: Dict[str, str]
) -> None:
    """Set SES notifications for an identity."""
    try:
        sns_bounce_arn = config["SNS_BOUNCE_ARN"]
        sns_complaint_arn = config["SNS_COMPLAINT_ARN"]
        sns_delivery_arn = config["SNS_DELIVERY_ARN"]

        notification_types = {
            "Bounce": sns_bounce_arn,
            "Complaint": sns_complaint_arn,
            "Delivery": sns_delivery_arn,
        }

        for notification_type, sns_topic_arn in notification_types.items():
            logger.info(
                f"Setting {notification_type} notification for {identity} with topic {sns_topic_arn}"
            )
            ses_client.set_identity_notification_topic(
                Identity=identity,
                NotificationType=notification_type,
                SnsTopic=sns_topic_arn,
            )
    except Exception as e:
        raise


def update_contact(
    contact_id: int, custom_fields: List[Dict[str, str]], config: Dict[str, str]
) -> Dict[str, Any]:
    """Update contact with custom fields."""
    try:
        keap_base_url = config["KEAP_BASE_URL"]
        keap_token = config["KEAP_API_KEY"]
        url = f"{keap_base_url}contacts/{contact_id}"
        headers = {
            "Authorization": f"Bearer {keap_token}",
            "Content-Type": "application/json",
        }
        payload = {"custom_fields": custom_fields}
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to update contact {contact_id}: {response.text}")
        logger.info(f"Updated contact {contact_id} with custom fields {custom_fields}")
        return response.json()
    except Exception as e:
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda function handler."""
    try:
        config = get_config()
        aws_clients = get_aws_clients()
        body = json.loads(event["body"])

        pwd = os.path.dirname(os.path.abspath(__file__))
        schema_path = f"{pwd}/schemas/input_schema.json"
        input_schema = load_schema(schema_path)
        validate(instance=body, schema=input_schema)

        contact_id = body["contact_id"]
        appname = body["appname"]
        email_username = body["email_username"]
        vanity_name = body["vanity_name"]

        first_name, last_name = query_rds(
            contact_id, appname, aws_clients["rds_client"], config=config
        )
        display_name = f"{first_name} {last_name}"
        email = f"{email_username}@{vanity_name}"
        password = generate_random_password()
        org_name = tldextract.extract(vanity_name).domain

        stack_id = create_workmail_stack(
            org_name,
            vanity_name,
            email_username,
            display_name,
            password,
            first_name,
            last_name,
            aws_clients["cloudformation_client"],
        )
        register_workmail_stack(
            contact_id,
            email_username,
            vanity_name,
            stack_id,
            aws_clients["rds_client"],
            config=config,
        )
        set_ses_notifications(email, aws_clients["ses_client"], config=config)
        dns_records = get_dns_records(
            vanity_name,
            aws_clients["ses_client"],
            aws_clients["workmail_client"],
            config=config,
        )
        update_contact(contact_id, dns_records, config=config)
        add_contact_to_group(contact_id, config["KEAP_TAG"], config=config)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "WorkMail organization and user creation initiated.",
                    "stackId": stack_id,
                    "email": email,
                }
            ),
        }
    except Exception as e:
        return handle_error(e)
