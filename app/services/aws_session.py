"""
AWS Session and Client Management for CloudSage.
Safely initializes boto3 sessions using the standard AWS credential chain.
"""

import logging
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.config import get_settings

logger = logging.getLogger("cloudsage.aws")


def get_aws_session() -> boto3.Session:
    """
    Creates and returns a boto3 Session.
    Prioritizes explicit settings if present, otherwise relies on the
    standard AWS credential chain (~/.aws/credentials, env vars, IAM roles).
    """
    settings = get_settings()

    session_kwargs: Dict[str, Any] = {}

    if settings.AWS_DEFAULT_REGION:
        session_kwargs["region_name"] = settings.AWS_DEFAULT_REGION

    if settings.AWS_PROFILE:
        session_kwargs["profile_name"] = settings.AWS_PROFILE

    # Optional explicit credentials from environment / .env
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.AWS_SESSION_TOKEN:
            session_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

    return boto3.Session(**session_kwargs)


def get_aws_client(service_name: str, session: Optional[boto3.Session] = None) -> Any:
    """
    Returns a boto3 client for the specified AWS service.
    """
    sess = session or get_aws_session()
    return sess.client(service_name)


def check_aws_connection(session: Optional[boto3.Session] = None) -> Dict[str, Any]:
    """
    Tests AWS connectivity by calling STS get_caller_identity.
    Returns status dict without exposing secret credentials.
    """
    sess = session or get_aws_session()
    region = sess.region_name or "us-east-1"

    try:
        sts_client = sess.client("sts")
        identity = sts_client.get_caller_identity()
        
        return {
            "connected": True,
            "account_id": identity.get("Account"),
            "arn": identity.get("Arn"),
            "user_id": identity.get("UserId"),
            "region": region,
            "message": "AWS connection successful"
        }
    except NoCredentialsError:
        return {
            "connected": False,
            "account_id": None,
            "arn": None,
            "region": region,
            "error_type": "NoCredentialsError",
            "message": "AWS credentials are not configured or are invalid"
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "ClientError")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        return {
            "connected": False,
            "account_id": None,
            "arn": None,
            "region": region,
            "error_type": error_code,
            "message": f"AWS connection failed: {error_msg}"
        }
    except BotoCoreError as e:
        return {
            "connected": False,
            "account_id": None,
            "arn": None,
            "region": region,
            "error_type": type(e).__name__,
            "message": f"AWS SDK error: {str(e)}"
        }
    except Exception as e:
        return {
            "connected": False,
            "account_id": None,
            "arn": None,
            "region": region,
            "error_type": "UnexpectedError",
            "message": f"Unexpected error checking AWS status: {str(e)}"
        }
