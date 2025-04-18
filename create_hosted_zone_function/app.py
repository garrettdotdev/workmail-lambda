# create_hosted_zone_function/app.py
import boto3
import logging
import os
import uuid
from typing import Dict, Any, List, Tuple

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_config():
    required_vars = [
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


def create_hosted_zone(
    domain_name: str,
    route53_client: boto3.client,
    config: Dict[str, Any],
) -> str:
    """Create a Route 53 Hosted Zone."""
    try:
        logger.info(f"Creating Route 53 hosted zone for domain {domain_name}")
        create_hosted_zone_response = route53_client.create_hosted_zone(
            Name=domain_name,
            VPC={
                "VPCRegion": config["VPC_REGION"],
                "VPCId": config["VPC_ID"],
            },
            CallerReference=str(uuid.uuid4()),
            HostedZoneConfig={
                "Comment": "WorkMail domain",
                "PrivateZone": False,
            },
            DelegationSetId=config["DELEGATION_SET_ID"],
        )
        hosted_zone_id = create_hosted_zone_response["HostedZone"]["Id"]
        logger.info(
            f"Created Route 53 hosted zone {hosted_zone_id} for domain {domain_name}"
        )
        return hosted_zone_id
    except Exception as e:
        raise e


def add_dns_records(
    hosted_zone_id: str,
    dns_records: List[Dict[str, str]],
    route53_client: boto3.client,
) -> None:
    """Add DNS records to a Route 53 Hosted Zone."""
    try:
        record_count = len(dns_records)
        logger.info(
            f"Adding {record_count} DNS records to Route 53 hosted zone {hosted_zone_id}"
        )
        real_count = 0
        for record in dns_records:
            recordtype = record["Type"]
            hostname = record["Hostname"]
            value = record["Value"]
            if recordtype == "TXT":
                value = f'"{value}"'
            route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    "Changes": [
                        {
                            "Action": "UPSERT",
                            "ResourceRecordSet": {
                                "Name": hostname,
                                "Type": recordtype,
                                "TTL": 300,
                                "ResourceRecords": [{"Value": value}],
                            },
                        }
                    ]
                },
            )
            real_count += 1
        logger.info(
            f"Added {real_count} DNS records to Route 53 hosted zone {hosted_zone_id}"
        )
    except Exception as e:
        raise e


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler."""
    logger.info(f"Event: {event}")
    try:
        config = get_config()
        route53_client = boto3.client("route53")
        hosted_zone_id = create_hosted_zone(
            event["vanity_name"], route53_client, config
        )
        dns_records = event["dns_records"]
        add_dns_records(hosted_zone_id, dns_records, route53_client)
        return event
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e
