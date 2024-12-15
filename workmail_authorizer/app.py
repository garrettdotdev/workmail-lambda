# workmail_authorizer/app.py
import json
import logging
import os
import jwt
import boto3
import botocore

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda Authorizer function for API Gateway HTTP API.
    Validates JWT token from 'Authorization' header and returns an IAM policy.

    Args:
        event (dict): The event payload from API Gateway.
        context (LambdaContext): The context in which the function is called.

    Returns:
        dict: An IAM policy to allow or deny the request.
    """
    logger.info(f"Event: {json.dumps(event)}")

    # Extract the token from the 'Authorization' header
    token = extract_token(event)
    if not token:
        logger.error("No token provided in the Authorization header.")
        return generate_policy("Deny", event["routeArn"])

    try:
        # Validate the JWT token
        decoded_token = verify_jwt_token(token)
        logger.info(f"Decoded Token: {decoded_token}")

        # Extract the principalId from the token (typically a user ID or subject)
        principal_id = decoded_token.get("sub", "user")

        # Generate an Allow policy for the user
        policy = generate_policy("Allow", event["routeArn"], principal_id)
        logger.info(f"Generated Policy: {policy}")
        return policy

    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return generate_policy("Deny", event["routeArn"])


def extract_token(event):
    """Extract the Bearer token from the Authorization header."""
    authorization_header = event.get("headers", {}).get("authorization", "")
    if authorization_header and authorization_header.lower().startswith("bearer "):
        return authorization_header.split(" ")[1]
    return None


def verify_jwt_token(token):
    """Verify the JWT token using a secret or public key."""
    secret_key = os.environ.get(
        "JWT_SECRET", "default-secret"
    )  # Get secret from env variable
    algorithms = os.environ.get("JWT_ALGORITHMS", "HS256").split(",")

    # Decode the JWT token
    decoded_token = jwt.decode(token, secret_key, algorithms=algorithms)
    return decoded_token


def generate_policy(effect, resource, principal_id="user"):
    """
    Generate an IAM policy.

    Args:
        effect (str): 'Allow' or 'Deny' for the policy effect.
        resource (str): The ARN of the resource being accessed.
        principal_id (str): The unique identifier for the user.

    Returns:
        dict: The policy document.
    """
    policy_document = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}
            ],
        },
    }
    return policy_document
