# create_workmail_org_function/app.py
import boto3
import json
import os
import logging
import uuid
import time
from typing import Dict, Any, List, Tuple
from workmail_common.utils import (
    process_input,
    connect_to_rds,
    get_aws_clients,
    keap_contact_create_note_via_proxy,
    keap_contact_add_to_group_via_proxy,
)

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_workmail_org(
    organization_name: str,
    vanity_name: str,
    workmail_client: Any,
) -> Dict[str, Any]:
    """Create a WorkMail Organization and User."""
    try:

        client_token = str(uuid.uuid4())
        # Create WorkMail organization
        logger.info(f"Creating WorkMail organization {organization_name}")
        create_org_response = workmail_client.create_organization(
            Alias=organization_name, ClientToken=client_token
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

        return {"organization_id": organization_id}
    except Exception as e:
        raise


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
        "KEAP_TAG_PENDING",
        "PROXY_ENDPOINT",
        "PROXY_ENDPOINT_HOST",
        "VPC_ID",
        "VPC_REGION",
        "DELEGATION_SET_ID",
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


def get_dns_records(
    organization_id: str,
    domain_name: str,
    workmail_client: boto3.client,
) -> List[Dict[str, str]]:
    """Get DNS records for a domain."""
    logger.info(f"Getting DNS records for domain {domain_name}")
    dns_records = []
    try:
        mail_domain_response = workmail_client.get_mail_domain(
            OrganizationId=organization_id, DomainName=domain_name
        )
        dns_records = mail_domain_response["Records"]
        logger.info(f"Retrieved DNS records for domain {domain_name}")
    except Exception as e:
        raise
    return dns_records


def get_client_info(
    contact_id: int,
    connection: Any,
) -> Tuple[str, str]:
    """Query RDS for customer information."""
    logger.info(f"Querying RDS for contact_id {contact_id}")
    try:
        cursor = connection.cursor()
        sql = """SELECT ownerfirstname, ownerlastname FROM app WHERE ownerid = %s LIMIT 1"""
        cursor.execute(sql, (contact_id,))
        result = cursor.fetchone()

        if not result:
            raise ValueError(f"No client found with contact_id {contact_id}")

        first_name, last_name = result
        logger.info(f"Retrieved client information for contact_id {contact_id}")
        return first_name, last_name
    except Exception as e:
        raise
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()


def prepare_keap_updates(dns_records: List[Dict[str, str]]) -> Dict[str, str]:
    """Prepare updates for the contact."""
    logger.info(f"Preparing DNS info to send to Keap")
    updates = {}
    try:
        for record in dns_records:
            recordtype = record["Type"]
            hostname = record["Hostname"]
            value = record["Value"]

            if recordtype == "MX":
                updates["API1"] = hostname
            elif "_amazonses" in hostname:
                updates["API2"] = value
            elif "_domainkey" in hostname:
                alnum_string = value.split(".")[0]
                if "API3" not in updates:
                    updates["API3"] = alnum_string
                elif "API4" not in updates:
                    updates["API4"] = alnum_string
                else:
                    updates["API5"] = alnum_string
        logger.info(f"Prepared DNS info to send to Keap: {updates}")
    except Exception as e:
        raise
    return updates


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
        sql = """INSERT INTO workmail_organizations (ownerid, email_username, vanity_name, organization_id, state) VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(
            sql, (ownerid, email_username, vanity_name, organization_id, "PENDING")
        )
        connection.commit()
        logger.info(
            f"Registered WorkMail organization {organization_id} for ownerid {ownerid}"
        )
    except Exception as e:
        raise
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()


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
        vanity_name = clean_input["vanity_name"]
        organization_name = clean_input["organization_name"]
        email_username = clean_input["email_username"]
        email_address = clean_input["email_address"]

        first_name, last_name = get_client_info(
            contact_id,
            connection,
        )

        create_workmail_response = create_workmail_org(
            organization_name,
            vanity_name,
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

        dns_records = get_dns_records(
            organization_id,
            vanity_name,
            aws_clients["workmail_client"],
        )

        # updates = prepare_keap_updates(dns_records)

        # keap_contact_create_note_via_proxy(
        #     contact_id, "workmail_dns_records", updates, config=config
        # )

        keap_contact_add_to_group_via_proxy(
            contact_id, int(config["KEAP_TAG_PENDING"]), config=config
        )

        logger.info("WorkMail organization and user creation initiated")

        return {
            "contact_id": contact_id,
            "organization_id": organization_id,
            "organization_name": organization_name,
            "email_username": email_username,
            "vanity_name": vanity_name,
            "email_address": email_address,
            "first_name": first_name,
            "last_name": last_name,
            "dns_records": dns_records,
        }
    except Exception as e:
        logger.exception(str(e))
        raise e
    finally:
        if "connection" in locals() and connection.is_connected():
            connection.close()
