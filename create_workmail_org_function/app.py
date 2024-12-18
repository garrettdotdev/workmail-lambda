import boto3
import json
import random
import string
import os
import requests
import logging
import mysql.connector
import uuid
import time
from botocore.config import Config
from config import get_config
from typing import Dict, Any, List, Tuple
from workmail_common.utils import (
    handle_error,
    process_input,
    connect_to_rds,
    get_aws_clients,
    get_secret,
)

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def add_contact_to_group(
    contact_id: int, tag_id: int, config: Dict[str, str]
) -> Dict[str, Any]:
    """Add contact to a group."""
    try:
        logger.info(f"Adding contact {contact_id} to tag {tag_id}")
        keap_base_url = config["KEAP_BASE_URL"]
        keap_token = get_secret(config["KEAP_API_KEY_SECRET_NAME"])
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


def create_workmail(
    org_name: str,
    vanity_name: str,
    email_username: str,
    first_name: str,
    last_name: str,
    workmail_client: Any,
) -> Dict[str, Any]:
    """Create a WorkMail Organization and User."""
    try:

        client_token = str(uuid.uuid4())
        # Create WorkMail organization
        logger.info(f"Creating WorkMail organization {org_name}")
        create_org_response = workmail_client.create_organization(
            Alias=org_name, ClientToken=client_token
        )
        organization_id = create_org_response["OrganizationId"]
        logger.info(f"Created WorkMail organization {organization_id}")

        # Wait for the organization to become Active
        logger.info(f"Waiting for organization {organization_id} to become Active")
        i = 0
        while True:
            describe_org_response = workmail_client.describe_organization(
                OrganizationId=organization_id
            )
            state = describe_org_response["State"].upper()
            if state == "ACTIVE":
                break
            elif state == "FAILED":
                raise ValueError(
                    f"Organization {organization_id} creation failed: {describe_org_response['ErrorMessage']}"
                )
            elif i > 10:
                raise ValueError(
                    f"Organization {organization_id} took too long to become Active"
                )
            time.sleep(2)
            i += 1

        # Register the domain
        logger.info(
            f"Registering domain {vanity_name} with organization {organization_id}"
        )
        workmail_client.register_mail_domain(
            ClientToken=client_token,
            OrganizationId=organization_id,
            DomainName=vanity_name,
        )
        logger.info(
            f"Registered domain {vanity_name} with organization {organization_id}"
        )

        # Create the WorkMail user
        logger.info(f"Creating WorkMail user {email_username}")
        display_name = f"{first_name} {last_name}"
        password = generate_random_password()
        create_user_response = workmail_client.create_user(
            OrganizationId=organization_id,
            Name=email_username,
            DisplayName=display_name,
            Password=password,
            Role="USER",
            FirstName=first_name,
            LastName=last_name,
            HiddenFromGlobalAddressList=False,
        )
        user_id = create_user_response["UserId"]
        logger.info(f"Created WorkMail user {email_username}, user_id {user_id}")

        return {
            "organization_id": organization_id,
            "user_id": user_id,
            "password": password,
        }
    except Exception as e:
        raise


def generate_random_password(length: int = 12) -> str:
    """Generate a random password."""
    logger.info(f"Generating random password of length {length}")
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choice(characters) for _ in range(length))


def get_dns_records(
    domain_name: str, ses_client: Any, workmail_client: Any, config: Dict[str, str]
) -> List[Dict[str, str]]:
    """Get DNS records for a domain."""
    logger.info(f"Getting DNS records for domain {domain_name}")
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
        logger.info(f"Retrieved DNS records for domain {domain_name}")
    except Exception as e:
        raise
    return dns_records


def get_client_info(
    contact_id: int,
    appname: str,
    connection: Any,
) -> Tuple[str, str]:
    """Query RDS for customer information."""
    logger.info(f"Querying RDS for contact_id {contact_id} and appname {appname}")
    try:
        cursor = connection.cursor()
        sql = """
        SELECT ownerfirstname, ownerlastname
        FROM app
        WHERE ownerid = %s AND appname = %s
        LIMIT 1
        """
        cursor.execute(sql, (contact_id, appname))
        result = cursor.fetchone()

        if not result:
            raise ValueError(
                f"No client found with contact_id {contact_id} and appname {appname}"
            )

        first_name, last_name = result
        logger.info(f"Retrieved client information for contact_id {contact_id}")
        return first_name, last_name
    except Exception as e:
        raise
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()


def register_workmail_organization(
    ownerid: int,
    email_username: str,
    vanity_name: str,
    organization_id: str,
    connection: Any,
) -> None:
    """Register a WorkMail stack in the database."""
    logger.info(f"Registering WorkMail stack {organization_id} for ownerid {ownerid}")
    try:
        cursor = connection.cursor()
        sql = """
        INSERT INTO workmail_organizations (ownerid, email_username, vanity_name, organization_id)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (ownerid, email_username, vanity_name, organization_id))
        connection.commit()
        logger.info(
            f"Registered WorkMail organization {organization_id} for ownerid {ownerid}"
        )
    except Exception as e:
        raise
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()


def set_ses_notifications(
    identity: str, ses_client: Any, config: Dict[str, str]
) -> None:
    """Set SES notifications for an identity."""
    logger.info(f"Setting SES notifications for identity {identity}")
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
        logger.info(f"Set SES notifications for identity {identity}")
    except Exception as e:
        raise


def update_contact(
    contact_id: int, custom_fields: List[Dict[str, str]], config: Dict[str, str]
) -> Dict[str, Any]:
    """Update contact with custom fields."""
    logger.info(f"Updating contact {contact_id} with custom fields {custom_fields}")
    try:
        keap_base_url = config["KEAP_BASE_URL"]
        keap_token = get_secret(config["KEAP_API_KEY_SECRET_NAME"])
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
    logger.info("Handling Lambda event")
    try:

        config = get_config()
        aws_clients = get_aws_clients()

        connection = connect_to_rds(aws_clients["secretsmanager_client"], config=config)

        body = json.loads(event["body"])

        pwd = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(pwd, "schemas/input_schema.json")
        clean_input = process_input(body, schema_path)

        contact_id = clean_input["contact_id"]
        appname = clean_input["appname"]
        vanity_name = clean_input["vanity_name"]
        org_name = clean_input["org_name"]
        email_username = clean_input["email_username"]
        email_address = clean_input["email_address"]

        first_name, last_name = get_client_info(
            contact_id,
            appname,
            connection,
        )

        create_workmail_response = create_workmail(
            org_name,
            vanity_name,
            email_username,
            first_name,
            last_name,
            aws_clients["workmail_client"],
        )
        organization_id = create_workmail_response["organization_id"]

        register_workmail_organization(
            contact_id,
            email_username,
            vanity_name,
            organization_id,
            connection,
        )

        set_ses_notifications(email_address, aws_clients["ses_client"], config=config)

        # dns_records = get_dns_records(
        #     vanity_name,
        #     aws_clients["ses_client"],
        #     aws_clients["workmail_client"],
        #     config=config,
        # )

        # update_contact(contact_id, dns_records, config=config)

        # add_contact_to_group(contact_id, config["KEAP_TAG"], config=config)

        logger.info("WorkMail organization and user creation initiated")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "WorkMail organization and user creation initiated.",
                    "stackId": organization_id,
                    "email": email_address,
                }
            ),
        }
    except Exception as e:
        return handle_error(e)
    finally:
        if "connection" in locals() and connection.is_connected():
            connection.close()
