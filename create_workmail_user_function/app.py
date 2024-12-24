# create_workmail_user_function/app.py
import logging
import os
import random
import string
from create_workmail_user_function.config import get_config
from typing import Any, Dict
from workmail_common.utils import (
    connect_to_rds,
    handle_error,
    get_aws_client,
    validate,
    update_contact,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_random_password(length: int = 12) -> str:
    """Generate a random password."""
    logger.info(f"Generating random password of length {length}")
    special_characters = "!@#$%^&*()"
    characters = string.ascii_letters + string.digits + special_characters
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice(special_characters),
    ]
    password += random.choices(characters, k=length - len(password))
    random.shuffle(password)
    return "".join(password)


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


def update_workmail_registration(contact_id, organization_id, connection):
    """Update the WorkMail registration for a contact."""
    try:
        logger.info(f"Updating WorkMail registration for contact {contact_id}")
        cursor = connection.cursor(dictionary=True)
        sql = """UPDATE workmail_organizations SET state = %s WHERE ownerid = %s AND organization_id = %s"""
        cursor.execute(
            sql,
            ("ACTIVE", contact_id, organization_id),
        )
        connection.commit()
        logger.info(
            f"Updated WorkMail registration to ACTIVE for organization {organization_id}"
        )
    except Exception as e:
        raise
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()


def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {event}")

        config = get_config()

        pwd = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(pwd, "schemas/input_schema.json")
        if not validate(event, schema_path):
            raise Exception("Input validation failed")

        contact_id = event["contact_id"]
        organization_id = event["organization_id"]
        organization_name = event["organization_name"]
        email_username = event["email_username"]
        email_address = event["email_address"]
        first_name = event["first_name"]
        last_name = event["last_name"]
        display_name = f"{first_name} {last_name}"

        password = generate_random_password()

        logger.info(
            f"Creating user {email_username} ({email_address}) in organization {organization_name} ({organization_id})"
        )

        workmail_client = get_aws_client("workmail")

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
        if not create_user_response:
            raise Exception("Failed to create user")
        user_id = create_user_response["UserId"]

        workmail_client.register_to_work_mail(
            OrganizationId=organization_id,
            UserId=user_id,
            Email=email_address,
        )

        secrets_manager_client = get_aws_client("secretsmanager")
        connection = connect_to_rds(secrets_manager_client, config)
        update_workmail_registration(contact_id, organization_id, connection)

        ses_client = get_aws_client("ses")
        set_ses_notifications(email_address, ses_client, config=config)

        custom_fields = {
            "API6": email_address,
            "API7": password,
            "API8": f"{organization_name}.awsapps.com/mail",
        }

        update_contact(contact_id, custom_fields, config)

        logger.info(f"User created successfully")
        return {"userCreated": True}

    except Exception as e:
        return handle_error(e)
